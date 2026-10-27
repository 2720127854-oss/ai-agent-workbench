"""后台 Worker：消费任务队列并执行（文档入库 / 跑评估）。

独立进程运行： python -m app.tasks.worker
配合 app.tasks.queue.TaskQueue 的 Redis Streams 使用。
"""
import asyncio
from app.db import init_db
from app.tasks.queue import TaskQueue
from app.rag.store import add_documents
from app.eval.judge import run_eval


async def handler(payload: dict):
    kind = payload.get("type")
    if kind == "ingest":
        docs = payload.get("docs", [])
        await add_documents(docs)
        print(f"[worker] 已入库 {len(docs)} 条文档")
    elif kind == "eval":
        dataset = payload.get("dataset", [])
        results = await run_eval(dataset)
        print(f"[worker] 评估完成，共 {len(results)} 条")
    else:
        print(f"[worker] 未知任务类型: {kind}")


async def main():
    await init_db()
    q = TaskQueue()
    print("[worker] 开始监听任务队列 ...")
    await q.consume(handler)


if __name__ == "__main__":
    asyncio.run(main())
