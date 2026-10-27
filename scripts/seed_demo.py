"""一键把演示文档切块入库（RAG）。

前置条件：
  - PostgreSQL(pgvector) 与 Redis 可连（docker compose 已起或本地已装）
  - .env 中 embedding_provider 已设为 openai 或 bge（真实中文 RAG）
    —— 用 openai 时确保 OPENAI_API_KEY 已填

运行： python scripts/seed_demo.py
"""
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.rag.store import add_documents
from app.rag.chunk import chunk_text

DEMO_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "demo" / "refund_policy.md"


async def main():
    await init_db()
    text = DEMO_PATH.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    docs = [{"content": c, "meta": {"source": "refund_policy.md"}} for c in chunks]
    await add_documents(docs)
    print(f"✅ 已入库 {len(docs)} 个片段（来自 {DEMO_PATH.name}）")
    print("下一步：curl -X POST http://localhost:8000/search -H 'Content-Type: application/json' -d '{\"query\":\"质量问题退货的运费谁承担\"}'")


if __name__ == "__main__":
    asyncio.run(main())
