"""pgvector 文档存储与向量检索。

对应 JD：RAG 的「检索」环节——用 PostgreSQL + pgvector 做向量库，
并用 <=> 余弦距离排序取 Top-K。相比 chromadb 单机版，pgvector 更易和
业务数据同库、便于事务与扩展。
"""
import json
from app.db import get_pool
from app.rag.embed import get_embedder


async def add_documents(docs: list[dict]):
    """批量入库。docs: [{"content": str, "meta": dict}, ...]"""
    emb = get_embedder()
    vecs = await emb.aencode([d["content"] for d in docs])
    pool = await get_pool()
    async with pool.acquire() as c:
        for d, v in zip(docs, vecs):
            await c.execute(
                "INSERT INTO documents(content, meta, embedding) "
                "VALUES($1, $2, $3::vector)",
                d["content"],
                json.dumps(d.get("meta", {})),
                str(v),
            )


async def similarity_search(query: str, k: int = 3) -> list[dict]:
    """向量检索：返回与 query 最相似的 k 条文档。

    注意：
      - asyncpg 返回 jsonb 为字符串，需手动 json.loads 还原成 dict；
      - 余弦距离运算符要求向量类型，必须 `$1::vector` 显式转换。
    """
    emb = get_embedder()
    qv = (await emb.aencode([query]))[0]
    pool = await get_pool()
    async with pool.acquire() as c:
        rows = await c.fetch(
            "SELECT content, meta FROM documents "
            "ORDER BY embedding <=> $1::vector LIMIT $2",
            str(qv), k,
        )
    out = []
    for r in rows:
        meta = r["meta"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        out.append({"content": r["content"], "meta": meta})
    return out
