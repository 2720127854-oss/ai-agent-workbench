"""FastAPI 入口：SSE 流式对话 + 文档入库 + 评估触发 + 成本指标。

对应 JD：流式输出（SSE）、流式一致性、会话状态管理、异步 API。
"""
import asyncio
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.db import init_db
from app.llm.providers import MultiModelRouter
from app.llm.agent import stream_turn, answer, last_provider
from app.llm.usage import UsageAccumulator
from app.memory.manager import save_turn, load_history
from app.rag.store import add_documents, similarity_search
from app.eval.judge import run_eval
from app.eval.cost import CostTracker
from app.tasks.queue import TaskQueue

app = FastAPI(title="AI Agent Workbench")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_FRONTEND = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "index.html"

router = MultiModelRouter()
cost = CostTracker()
queue = TaskQueue()


class ChatRequest(BaseModel):
    session: str = "default"
    message: str = ""


class DocRequest(BaseModel):
    docs: list[dict] = []  # [{"content": str, "meta": dict}]


class SearchRequest(BaseModel):
    query: str = ""
    k: int = 3


@app.on_event("startup")
async def startup():
    await init_db()
    if not router.available:
        print("⚠️  未配置任何 LLM 供应商，请在 .env 填入 DEEPSEEK_API_KEY / OPENAI_API_KEY")


@app.get("/health")
async def health():
    return {"status": "ok", "llm_ready": router.available}


@app.get("/")
async def index():
    """极简聊天 UI（同源托管，便于演示与录屏）。"""
    return FileResponse(_FRONTEND)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式对话：边生成边返回 token。"""
    if not router.available:
        return EventSourceResponse(_err("未配置 LLM 供应商"))
    if not await router.acquire():
        return EventSourceResponse(_err("请求过于频繁，请稍后再试"))

    async def event_gen():
        history = await load_history(req.session, n=10)
        usage = UsageAccumulator()
        full = []
        async for token in stream_turn(req.message, history, usage=usage):
            full.append(token)
            yield {"event": "token", "data": token}
        text = "".join(full)
        await save_turn(req.session, "user", req.message)
        await save_turn(req.session, "ai", text)
        # 真实 token 计量：优先用模型返回的 usage，拿不到再兜底估算
        model = last_provider() or ""
        if usage.total > 0:
            await cost.add_usage(usage.prompt, usage.completion, model)
        else:
            await cost.add_estimate(len(text), model)
        yield {"event": "meta", "data": f"{model} (tokens={usage.total})"}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_gen())


@app.post("/documents")
async def upload_docs(req: DocRequest):
    """同步入库（小批量）；大批量建议走 /documents/async 入队。"""
    if not req.docs:
        return {"ok": False, "msg": "docs 不能为空"}
    await add_documents(req.docs)
    return {"ok": True, "count": len(req.docs)}


@app.post("/documents/async")
async def upload_docs_async(req: DocRequest):
    """异步入库：把任务丢进 Redis 队列，由 worker 消费（解耦耗时任务）。"""
    await queue.enqueue({"type": "ingest", "docs": req.docs})
    return {"ok": True, "queued": len(req.docs)}


@app.post("/search")
async def search(req: SearchRequest):
    """检索调试接口：直接看 RAG 召回了哪些片段（用于演示与调参）。"""
    rows = await similarity_search(req.query, k=req.k)
    return {"query": req.query, "hits": rows}


@app.post("/eval")
async def trigger_eval(dataset: list[dict]):
    """触发 LLM-as-judge 评估（同步跑完返回结果）。"""
    results = await run_eval(dataset)
    return {"ok": True, "results": results}


@app.get("/metrics")
async def metrics():
    return await cost.snapshot()


async def _err(msg: str):
    yield {"event": "error", "data": msg}
