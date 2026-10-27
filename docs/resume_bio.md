# 简历「项目经历」文案

> 用途：投递「AI 应用开发工程师」类岗位时，放在简历项目经历栏。
> 风格：动词开头、技术点对齐 JD、不夸大（个人项目即写「独立开发」）。

---

## 版本一：项目经历栏（推荐，3 条要点）

**多模型 Agent 对话工作台**（独立开发 | Python）
- 基于 FastAPI + asyncio 实现 SSE 流式对话，用 LangGraph 编排 Agent 完成 Function Calling 与多步执行；封装 DeepSeek / OpenAI 多模型接入层，支持自动降级、重试与限流。
- 搭建 PostgreSQL + pgvector 中文 RAG 检索（按段落+句切块、BGE / OpenAI 向量化），以 Redis 承载限流与消息队列，异步解耦入库 / 评测任务。
- 落地 LLM-as-judge 评测体系与基于模型真实 token usage 的成本统计，支撑效果回归与成本优化。

**技术栈**：Python · FastAPI · LangGraph · pgvector · Redis · Docker

---

## 版本二：作品集标题下的一句话

一个覆盖 asyncio 流式、LangGraph Agent、多模型自动降级、中文 RAG、消息队列与评测成本的 LLM 应用骨架，可 `docker compose` 一键部署。

---

## 版本三：面试自我介绍里的一句钩子

「我做了一个多模型 Agent 工作台，把流式对话、RAG、多供应商降级和评测成本串成一套能一键部署的系统，正好对应你们 JD 里那几条工程要求。」
