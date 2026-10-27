"""向量化器：入库与检索必须用同一个实例，否则维度/分布不一致会检索失效。

可切换三种 provider（对应 JD：朴素 RAG「切块—Embedding—检索」的 Embedding 环节）：
  - fake   ：确定性伪向量，零依赖跑通全链路（默认，无需任何 Key）
  - openai ：调用 OpenAI embeddings，真实中文能力、无需 torch，最易跑通「真·中文 RAG」
  - bge    ：本地 BGE 中文向量（中文效果最好，需 sentence-transformers + 模型权重）

面试可以讲：为什么默认不选 chromadb 的 all-MiniLM（对中文无效），以及
不同场景在「效果 / 成本 / 部署复杂度」之间怎么权衡。
"""
import hashlib
import math
from app.config import settings

_embedder = None


class FakeEmbedder:
    """不依赖任何模型：把文本哈希成固定维度向量并归一化。仅用于本地跑通流程。"""
    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode(self, texts):
        out = []
        for t in texts:
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            vec = [((h >> (i * 3)) & 1023) / 1023.0 - 0.5 for i in range(self.dim)]
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out

    async def aencode(self, texts):
        return self.encode(texts)


class OpenAIEmbedder:
    """调用 OpenAI 兼容 embeddings 接口（需 OPENAI_API_KEY）。"""
    def __init__(self, model: str):
        from openai import AsyncOpenAI
        if not settings.openai_api_key:
            raise RuntimeError("使用 openai embedding 需要配置 OPENAI_API_KEY")
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = model
        # text-embedding-3-small 默认 1536 维；如需其它模型在此对齐维度
        self.dim = 1536 if "3-small" in model else 1536

    async def _encode_async(self, texts):
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

    async def aencode(self, texts):
        return await self._encode_async(texts)

    def encode(self, texts):
        # 同步包装：在已有事件循环内用 asyncio.run 会冲突，故要求调用方在 async 上下文使用 aencode
        raise RuntimeError("OpenAIEmbedder 请使用 aencode（在 async 上下文中）")


class BGEEmbedder:
    """本地 BGE 中文向量化（需 sentence-transformers 与模型权重）。"""
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    async def aencode(self, texts):
        return self.encode(texts)


def get_embedder():
    """单例：整个进程共用一个 embedder，保证入库/检索维度一致。

    注意：切换 provider 后向量维度会变，需 reset_db 重建 documents 表再入库。
    """
    global _embedder
    if _embedder is not None:
        return _embedder

    provider = settings.embedding_provider.lower()
    if provider == "openai":
        _embedder = OpenAIEmbedder(settings.openai_embed_model)
    elif provider == "bge":
        _embedder = BGEEmbedder(settings.bge_model)
    else:
        dim = settings.embedding_dim or 384
        _embedder = FakeEmbedder(dim)
    return _embedder
