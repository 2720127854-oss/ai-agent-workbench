"""跑评估集：用 LLM-as-judge 给 Agent 在演示知识库上的表现打分。

前置：已 seed 知识库（python scripts/seed_demo.py），且 .env 配好 LLM Key。
运行： python scripts/run_eval.py
结果会写入 eval_runs 表，并打印每条得分与平均分，用于「改了 Prompt/检索策略后
效果变好还是变差」的回归对比。
"""
import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.eval.judge import run_eval

DATASET = pathlib.Path(__file__).resolve().parents[1] / "data" / "eval" / "refund_qa.json"


async def main():
    await init_db()
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    print(f"加载评测集：{len(dataset)} 条")
    results = await run_eval(dataset)
    total = sum(r["score"] for r in results)
    print("\n=== 评测结果 ===")
    for r in results:
        print(f"  Q: {r['question']}\n  得分: {r['score']}  理由: {r['reason']}")
    print(f"\n平均分：{total / len(results):.2f} / 10")


if __name__ == "__main__":
    asyncio.run(main())
