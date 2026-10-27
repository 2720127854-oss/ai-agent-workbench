"""切换 embedding_provider 后，向量维度会变，需重建 documents 表再入库。

运行： python scripts/reset_db.py
会清空 documents 表（不影响 messages / eval_runs）。重建后请重新跑 seed_demo.py。
"""
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db import get_pool


async def main():
    pool = await get_pool()
    async with pool.acquire() as c:
        await c.execute("DROP TABLE IF EXISTS documents;")
    print("✅ 已清空 documents 表。请重新运行 scripts/seed_demo.py 入库。")


if __name__ == "__main__":
    asyncio.run(main())
