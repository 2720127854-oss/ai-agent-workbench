"""Agent 可调用的工具集（Function Calling）。

这里先放一个 RAG 检索工具作为示例。JD 要求的 function calling 就是让模型
决定何时调用这些工具——比如用户问到具体业务/文档内容时，模型自动触发 rag_search。

可扩展工具：查天气、查数据库、调用图片生成 API 等，都按同样的 @tool 形式加进来。
"""
import json
from langchain_core.tools import tool
from app.rag.store import similarity_search


@tool
async def rag_search(query: str) -> str:
    """在本地知识库中检索与问题相关的资料。当用户问到具体业务、文档、产品说明时调用。"""
    rows = await similarity_search(query, k=3)
    if not rows:
        return "知识库暂时没有相关内容，请先通过 /documents 接口上传资料。"
    parts = []
    for i, r in enumerate(rows):
        meta = r.get("meta") or {}
        source = meta.get("source", "未知来源")
        parts.append(f"[{i+1}] 出处：{source}\n{r['content']}")
    return "\n\n".join(parts)
