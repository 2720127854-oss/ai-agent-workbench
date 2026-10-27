"""Agent 编排层：基于 LangGraph 的 ReAct Agent（思考—调用工具—再思考）。

对应 JD：Agent 框架（LangGraph）、意图路由、Function Calling、多步执行。
create_react_agent 内部就是一张 StateGraph：agent 节点 → tools 节点，
条件边判断「是否还要继续调用工具」，直到给出最终答复。
"""
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from app.config import settings
from app.llm.providers import MultiModelRouter
from app.llm.tools import tools
from app.llm.usage import UsageAccumulator, TokenUsageCallback

_router = MultiModelRouter()
_agent_cache: dict[int, object] = {}   # idx -> 编译好的 Agent（按供应商缓存）
_last_provider: str | None = None


def get_agent(idx: int = 0):
    """按供应商索引取（或构建）Agent，结果按 idx 缓存复用。"""
    if idx not in _agent_cache:
        model = _router.client_at(idx)
        _agent_cache[idx] = create_react_agent(model, tools)
    return _agent_cache[idx]


def last_provider() -> str | None:
    """最近一次成功作答所用的供应商，便于日志/可观测。"""
    return _last_provider


def _to_messages(history: list[tuple[str, str]], query: str):
    msgs = []
    for role, content in history:
        msgs.append(HumanMessage(content) if role == "user" else AIMessage(content))
    msgs.append(HumanMessage(query))
    return msgs


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # 多模态/多段情况
        return "".join(
            p["text"] for p in content
            if isinstance(p, dict) and p.get("type") == "text"
        )
    return ""


async def stream_turn(query: str, history: list[tuple[str, str]], usage: UsageAccumulator | None = None):
    """流式生成（供 SSE），带跨供应商 failover。

    失败转移规则：
      - 尚未吐出任何 token 时异常 → 切到下一个供应商整体重试；
      - 已经吐出 token 后异常 → 无法干净回滚，直接抛出（避免返回半截答案）。
    这样上游某个供应商 5xx / 限流 / 超时，会自动切到下一个，对调用方透明。
    usage：传入则记录本次回合的真实 token 用量（跨多步调用累加）。
    """
    if _router.provider_count == 0:
        raise RuntimeError("未配置任何 LLM 供应商，请在 .env 填入 API Key")

    cb = [TokenUsageCallback(usage)] if usage else None
    idx, last_err = 0, None
    while idx < _router.provider_count:
        try:
            agent = get_agent(idx)
            inputs = {"messages": _to_messages(history, query)}
            emitted = False
            async for event in agent.astream_events(inputs, version="v2", config={"callbacks": cb} if cb else None):
                if event["event"] == "on_chat_model_stream":
                    piece = _extract_text(event["data"]["chunk"].content)
                    if piece:
                        emitted = True
                        yield piece
            _last_provider = _router.name_at(idx)
            return
        except Exception as e:  # 上游异常 → failover
            last_err = e
            if emitted:          # 已输出部分内容，不能干净切换
                raise
            print(f"[failover] 供应商 {_router.name_at(idx)} 失败：{e}，切换下一个")
            idx += 1
    if last_err:
        raise last_err
    raise RuntimeError("所有 LLM 供应商均不可用")


async def answer(query: str, history: list[tuple[str, str]], usage: UsageAccumulator | None = None) -> str:
    """非流式一次性返回（评估/后台任务用），同样带 failover。"""
    if _router.provider_count == 0:
        raise RuntimeError("未配置任何 LLM 供应商，请在 .env 填入 API Key")

    cb = [TokenUsageCallback(usage)] if usage else None
    last_err = None
    for idx in range(_router.provider_count):
        try:
            agent = get_agent(idx)
            res = await agent.ainvoke(
                {"messages": _to_messages(history, query)},
                config={"callbacks": cb} if cb else None,
            )
            _last_provider = _router.name_at(idx)
            return res["messages"][-1].content
        except Exception as e:
            last_err = e
            print(f"[failover] 供应商 {_router.name_at(idx)} 失败：{e}，切换下一个")
    if last_err:
        raise last_err
    raise RuntimeError("所有 LLM 供应商均不可用")
