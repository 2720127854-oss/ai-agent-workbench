"""Token 成本追踪（JD 加分项：Token 成本优化与可观测）。

把每次调用的真实 token 数与估算美元成本累计进 Redis，供 /metrics 接口查看，
帮助回答「这个 Agent 跑一轮花多少钱、哪个供应商/环节最贵」。
"""
import redis.asyncio as redis
from app.config import settings

# 各模型每 1K token 参考成本（USD，取输入输出均值近似）。按需补全。
_COST_PER_1K = {
    "deepseek-chat": 0.00014,
    "gpt-4o-mini": 0.00015,
    "text-embedding-3-small": 0.00002,
}


class CostTracker:
    def __init__(self):
        self.r = redis.from_url(settings.redis_url, decode_responses=True)

    async def add_usage(self, prompt_tokens: int, completion_tokens: int, model: str = ""):
        """写入真实用量（来自模型 usage）。"""
        total = (prompt_tokens or 0) + (completion_tokens or 0)
        rate = _COST_PER_1K.get(model, 0.00015)
        cost = total / 1000.0 * rate
        await self.r.incrby("cost:tokens", total)
        await self.r.incrbyfloat("cost:usd", cost)

    async def add_estimate(self, text_len: int, model: str = ""):
        """拿不到真实 usage 时的兜底估算（字符数 / 4 近似 token 数）。"""
        tokens = max(1, text_len // 4)
        await self.add_usage(tokens, 0, model or settings.deepseek_model)

    async def snapshot(self) -> dict:
        tokens = int(await self.r.get("cost:tokens") or 0)
        usd = float(await self.r.get("cost:usd") or 0.0)
        return {"tokens": tokens, "usd": round(usd, 4)}
