#!/usr/bin/env bash
# 一键跑起项目（解决「沙箱无 Docker」：在你本机、已装 Docker Desktop 后运行）
# 用法： bash scripts/run.sh
set -e
cd "$(dirname "$0")/.."

# 1) 准备 .env（已存在则跳过）
if [ ! -f .env ]; then
  cp .env.example .env
  echo "已生成 .env，请打开填入 OPENAI_API_KEY 并把 embedding_provider 设为 openai"
fi

# 2) 起 Postgres + Redis + API
docker compose up -d --build

# 3) 等 API 就绪后初始化并灌入演示知识库
echo "等待服务就绪 ..."
sleep 8
docker compose exec api python scripts/reset_db.py
docker compose exec api python scripts/seed_demo.py

echo ""
echo "完成。浏览器打开 http://localhost:8000"
echo "  - 右侧检索：质量问题退货的运费谁承担"
echo "  - 左侧对话：根据知识库，退款多久到账？"
