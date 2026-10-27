"""中文友好的切块器。

对应 JD 的「朴素切块为什么会翻车」：
- 按固定字数硬切，会把一句话/一个条款拦腰截断，检索召回的片段语义不完整
- 这里先按「标题/空行/标点」做段落级切分，再在超长段落内按句切分并带重叠，
  尽量保证每个 chunk 语义自洽，降低检索噪声。

可调参数：max_chars（单块上限）、overlap（相邻块重叠字数，避免边界信息丢失）。
"""
import re

_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")
_BLOCK_SPLIT = re.compile(r"\n\s*\n|#{1,6}\s*")


def chunk_text(text: str, max_chars: int = 220, overlap: int = 40) -> list[str]:
    text = text.strip()
    if not text:
        return []

    # 1) 先按标题/空行切成大块
    blocks = [b.strip() for b in _BLOCK_SPLIT.split(text) if b and b.strip()]

    chunks: list[str] = []
    for block in blocks:
        if len(block) <= max_chars:
            chunks.append(block)
            continue
        # 2) 超长段落按句切分，带重叠拼接
        sentences = [s.strip() for s in _SENT_SPLIT.split(block) if s and s.strip()]
        buf = ""
        for sent in sentences:
            if len(buf) + len(sent) > max_chars and buf:
                chunks.append(buf)
                buf = buf[-overlap:] + sent if overlap else sent
            else:
                buf += sent
        if buf:
            chunks.append(buf)

    # 去重 + 去空白
    seen = set()
    out = []
    for c in chunks:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
