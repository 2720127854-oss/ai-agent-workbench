"""数据库连接池：PostgreSQL(asyncpg) + pgvector，以及 Redis 异步客户端。

集中管理一个连接池，避免每个请求都新建连接（JD 要求的数据建模 / 长期记忆都靠它）。
"""
import asyncpg
from app.config import settings
from app.rag.embed import get_embedder

_pool = None


async def get_pool():
    """返回全局唯一的 asyncpg 连接池（懒加载单例）。"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.postgres_dsn, min_size=1, max_size=5
        )
    return _pool


async def init_db():
    """建表：带向量列的文档表（RAG）、对话消息表（记忆）、评估记录表。

    向量维度取自当前 embedder，保证「入库」和「检索」用同一维度。
    """
    emb = get_embedder()
    dim = emb.dim
    pool = await get_pool()
    async with pool.acquire() as c:
        await c.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await c.execute(
            f"""
            CREATE TABLE IF NOT EXISTS documents (
                id      SERIAL PRIMARY KEY,
                content TEXT,
                meta    JSONB,
                embedding vector({dim})
            );
            """
        )
        # ivfflat 近似索引：数据量大时检索更稳（lists 随数据量调整）
        await c.execute(
            f"""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx
            ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists=10);
            """
        )
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id      SERIAL PRIMARY KEY,
                session TEXT,
                role    TEXT,
                content TEXT,
                ts      TIMESTAMPTZ DEFAULT now()
            );
            """
        )
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_runs (
                id          SERIAL PRIMARY KEY,
                question    TEXT,
                answer      TEXT,
                reference   TEXT,
                score       REAL,
                judge_model TEXT,
                ts          TIMESTAMPTZ DEFAULT now()
            );
            """
        )
