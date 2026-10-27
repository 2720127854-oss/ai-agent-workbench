"""轻量任务队列：基于 Redis Streams 的异步任务（JD：消息队列 / 至少一次投递）。

用法场景：文档入库、跑评估这类耗时任务，从 API 请求中解耦出去异步执行，
避免阻塞 HTTP 请求（配合 worker.py 消费）。
保留「至少一次投递」语义：消费成功后 XACK 确认。
"""
import json
import redis.asyncio as redis
from app.config import settings


class TaskQueue:
    def __init__(self, name: str = "tasks"):
        self.r = redis.from_url(settings.redis_url, decode_responses=True)
        self.name = name
        self.group = f"{name}-cg"

    async def setup(self):
        try:
            await self.r.xgroup_create(self.name, self.group, id="0", mkstream=True)
        except Exception:
            pass  # 已存在则忽略

    async def enqueue(self, payload: dict) -> str:
        return await self.r.xadd(self.name, {"payload": json.dumps(payload)})

    async def consume(self, handler, block_ms: int = 5000):
        await self.setup()
        while True:
            resp = await self.r.xreadgroup(self.group, "worker", {self.name: ">"}, block=block_ms)
            if not resp:
                continue
            for _stream, messages in resp:
                for msg_id, fields in messages:
                    payload = json.loads(fields["payload"])
                    try:
                        await handler(payload)
                    finally:
                        await self.r.xack(self.name, self.group, msg_id)
