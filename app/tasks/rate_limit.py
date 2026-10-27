"""基于 Redis 的滑动窗口限流器（令牌桶的简化实现）。

对应 JD：异步 API 的限流设计——保护上游 LLM 不被打爆、控制成本。
面试可讲：为什么用 Redis（多实例共享状态）、滑动窗口 vs 固定窗口的区别。
"""
import time
import redis.asyncio as redis
from app.config import settings


class RateLimiter:
    def __init__(self):
        self.r = redis.from_url(settings.redis_url, decode_responses=True)
        self.cap = settings.rate_limit_per_min

    async def allow(self, key: str = "global") -> bool:
        now = time.time()
        # 清掉 60s 前的请求记录
        await self.r.zremrangebyscore(key, 0, now - 60)
        count = await self.r.zcard(key)
        if count >= self.cap:
            return False
        await self.r.zadd(key, {str(now): now})
        return True
