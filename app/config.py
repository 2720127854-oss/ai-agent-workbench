"""全局配置：从 .env 读取，集中管理多模型、存储、RAG、限流等开关。

对应 JD：这是整个系统的「配置中枢」，面试时可说明
- 多供应商通过环境变量切换，无需改代码
- 限流、向量维度等参数外置，便于压测与调优
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---- 多模型接入层：均兼容 OpenAI chat completions 协议 ----
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # ---- 存储 ----
    postgres_dsn: str = "postgres://app:app@localhost:5432/agentdb"
    redis_url: str = "redis://localhost:6379/0"

    # ---- RAG 向量化 ----
    # provider 可切换：
    #   fake   —— 确定性伪向量，不依赖任何模型，本地零依赖跑通全链路（默认）
    #   openai —— 调用 OpenAI embeddings（text-embedding-3-small），真实中文 RAG、无需 torch
    #   bge    —— 本地 BGE 中文向量（效果最好，需 sentence-transformers 与模型权重）
    embedding_provider: str = "fake"
    openai_embed_model: str = "text-embedding-3-small"
    bge_model: str = "BAAI/bge-small-zh-v1.5"
    # 向量维度：0 表示由 provider 自动探测；fake 时若需固定可手动填
    embedding_dim: int = 0

    # ---- 限流（令牌桶：每分钟允许请求数）----
    rate_limit_per_min: int = 30

    # ---- 评估 ----
    eval_judge_model: str = ""  # 不填则用主模型当裁判


settings = Settings()
