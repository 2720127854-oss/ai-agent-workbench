"""一键把演示文档切块入库（RAG）。

前置条件：
  - PostgreSQL(pgvector) 与 Redis 可连（docker compose 已起或本地已装）
  - embedding_provider 可设为 fake / openai / bge 任一：
      fake（默认）= 确定性伪向量，零依赖即可跑通全链路（检索为哈希模拟，非语义相关）
      openai     = 真实中文 embeddings（需 OPENAI_API_KEY，国内需代理）
      bge        = 本地 BGE 中文向量（需 sentence-transformers 与模型权重）

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
