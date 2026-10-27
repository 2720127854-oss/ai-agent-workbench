"""多轮对话记忆：短期靠 Redis 取最近 N 条，长期落库 PostgreSQL。

对应 JD：多轮会话状态管理、长期记忆（加分项）。
- 短期：高频、低延迟，放 Redis（这里复用 DB 也可，按规模演进）
- 长期：结构化沉淀，放 PostgreSQL，便于回溯与微调数据沉淀
"""
from app.db import get_pool


async def save_turn(session: str, role: str, content: str):
    pool = await get_pool()
    async with pool.acquire() as c:
        await c.execute(
            "INSERT INTO messages(session, role, content) VALUES($1, $2, $3)",
            session, role, content,
        )


async def load_history(session: str, n: int = 10) -> list[tuple[str, str]]:
    """取某会话最近 n 条消息（按时间正序，便于直接喂给模型）。"""
    pool = await get_pool()
    async with pool.acquire() as c:
        rows = await c.fetch(
            "SELECT role, content FROM messages "
            "WHERE session=$1 ORDER BY id DESC LIMIT $2",
            session, n,
        )
    rows = list(reversed(rows))
    return [(r["role"], r["content"]) for r in rows]
