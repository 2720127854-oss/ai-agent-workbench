FROM python:3.11-slim

WORKDIR /app

# 系统依赖（asyncpg 等需要编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 国内加速：使用清华 PyPI 镜像（国外源常被墙/超时），通用源兜底
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://pypi.org/simple -r requirements.txt

COPY . .

# 容器内默认把 .env.example 复制为 .env（如需真实密钥请用挂载卷覆盖）
RUN if [ ! -f .env ]; then cp .env.example .env; fi

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
