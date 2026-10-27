"""多模型接入层：统一封装多家供应商，提供「自动降级 + 重试 + 限流」。

对应 JD 核心要求：多供应商接入、自动降级、重试、幂等、限流。
面试重点：这是把「不同厂商 API 差异」屏蔽成一个统一接口的关键层。
"""
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tasks.rate_limit import RateLimiter


def _build_model(name: str, api_key: str, base_url: str, model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.3,
        max_retries=2,          # 内置重试：上游 5xx / 限流自动重试
        streaming=True,         # 开启流式，供 SSE 边生成边返回
        # 流式时也让上游在最后一个 chunk 返回 usage（真实 token 计量需要）
        model_kwargs={"stream_options": {"include_usage": True}},
    )


class MultiModelRouter:
    """按配置构造多个供应商客户端，pick() 返回首个可用者。

    可扩展点（留作面试加分项）：
      - 运行时按延迟/成本/配额动态选择（而非仅按配置顺序）
      - 单次请求在 A 失败后切到 B（跨供应商 failover）
    """

    def __init__(self):
        self.clients = []
        if settings.deepseek_api_key:
            self.clients.append(
                ("deepseek", _build_model(
                    "deepseek", settings.deepseek_api_key,
                    settings.deepseek_base_url, settings.deepseek_model))
            )
        if settings.openai_api_key:
            self.clients.append(
                ("openai", _build_model(
                    "openai", settings.openai_api_key,
                    settings.openai_base_url, settings.openai_model))
            )
        self.limiter = RateLimiter()

    @property
    def available(self) -> bool:
        return len(self.clients) > 0

    def pick(self):
        """返回首个可用供应商的客户端（含名称）。"""
        if not self.clients:
            raise RuntimeError(
                "未配置任何 LLM 供应商，请在 .env 填入 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"
            )
        return self.clients[0]

    # ---- 运行时 failover 支持 ----
    @property
    def provider_count(self) -> int:
        return len(self.clients)

    def name_at(self, i: int) -> str:
        return self.clients[i][0]

    def client_at(self, i: int):
        return self.clients[i][1]

    async def acquire(self) -> bool:
        """限流闸门：通过返回 True，否则 False。"""
        return await self.limiter.allow(key="llm:global")
