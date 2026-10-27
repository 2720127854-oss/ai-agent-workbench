"""评估模块：LLM-as-judge 自动打分（JD 加分项：评测体系）。

思路：准备一批 (问题, 参考答案) 数据集，让 Agent 作答，再让裁判模型
按 0-10 打分并给出理由，结果落库 eval_runs，用于回归对比「改了 Prompt/检索
策略后效果变好还是变差」。
"""
import asyncpg
from langchain_openai import ChatOpenAI
from app.config import settings
from app.llm.agent import answer
from app.llm.usage import UsageAccumulator, TokenUsageCallback
from app.eval.cost import CostTracker
from app.db import get_pool


JUDGE_PROMPT = """你是一名严格的评分员。请根据参考答案，对「模型回答」的质量打分（0-10）。
只输出 JSON：{{"score": <数字>, "reason": "<简短理由>"}}
问题：{q}
参考答案：{ref}
模型回答：{ans}
"""


async def _judge(question: str, reference: str, ans: str) -> tuple[float, str]:
    model = settings.eval_judge_model or settings.deepseek_model or settings.openai_model
    # 若有对应供应商 key 则用它；否则复用主模型
    if settings.eval_judge_model:
        client = ChatOpenAI(model=model, api_key=settings.openai_api_key or settings.deepseek_api_key,
                            base_url=settings.openai_base_url if settings.openai_api_key else settings.deepseek_base_url)
    else:
        from app.llm.providers import MultiModelRouter
        client = MultiModelRouter().client_at(0)
    acc = UsageAccumulator()
    msg = await client.ainvoke(
        JUDGE_PROMPT.format(q=question, ref=reference, ans=ans),
        config={"callbacks": [TokenUsageCallback(acc)]},
    )
    text = msg.content
    try:
        import json, re
        obj = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        return float(obj["score"]), obj.get("reason", ""), acc
    except Exception:
        return 0.0, f"解析失败：{text[:200]}", acc


async def run_eval(dataset: list[dict], session_prefix: str = "eval"):
    """dataset: [{"question": ..., "reference": ...}, ...]
    返回每条评分汇总，并把结果与真实 token 用量写入成本追踪。
    """
    pool = await get_pool()
    tracker = CostTracker()
    results = []
    for i, item in enumerate(dataset):
        session = f"{session_prefix}-{i}"
        ans_acc = UsageAccumulator()
        ans = await answer(item["question"], [], usage=ans_acc)
        score, reason, judge_acc = await _judge(item["question"], item.get("reference", ""), ans)
        # 记录真实 token 成本（Agent 作答 + 裁判打分）
        await tracker.add_usage(ans_acc.prompt, ans_acc.completion, "agent")
        await tracker.add_usage(judge_acc.prompt, judge_acc.completion, "judge")
        async with pool.acquire() as c:
            await c.execute(
                "INSERT INTO eval_runs(question, answer, reference, score, judge_model) "
                "VALUES($1,$2,$3,$4,$5)",
                item["question"], ans, item.get("reference", ""), score,
                settings.eval_judge_model or "primary",
            )
        results.append({"question": item["question"], "score": score, "reason": reason})
    return results
