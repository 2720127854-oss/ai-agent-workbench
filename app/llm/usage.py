"""真实 Token 计量：用 LangChain callback 抓取每次 LLM 调用的 usage。

对应 JD 加分项「Token 成本优化与可观测」。之前是 len(text)//4 的粗略估算，
这里改为从模型的 usage（prompt_tokens / completion_tokens）取真实值，
跨 Agent 多步调用自动累加，供成本追踪使用。
"""
import threading
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult


class UsageAccumulator:
    """线程安全的 token 累加器（一个对话回合内的多次 LLM 调用汇总到这里）。"""
    def __init__(self):
        self.prompt = 0
        self.completion = 0
        self._lock = threading.Lock()

    def add(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        with self._lock:
            self.prompt += prompt_tokens or 0
            self.completion += completion_tokens or 0

    @property
    def total(self) -> int:
        return self.prompt + self.completion


class TokenUsageCallback(AsyncCallbackHandler):
    """LangChain 异步回调：在每次 LLM 调用结束时提取 token_usage。"""
    def __init__(self, acc: UsageAccumulator):
        self.acc = acc

    async def on_llm_end(self, output: LLMResult, **kwargs):
        try:
            usage = (output.llm_output or {}).get("token_usage") or {}
            self.acc.add(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
        except Exception:
            pass  # 拿不到 usage 不影响主流程
