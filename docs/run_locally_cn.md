# 本地运行手册（中国网络环境）

> 本仓库默认支持离线跑通全链路：LLM 用 **DeepSeek**（国内直连），向量化用 **fake**（零模型下载）。
> 只需安装 Docker Desktop + 一个 DeepSeek API Key，无需翻墙、无需下载任何模型权重。

---

## 0. 前置：拿到 DeepSeek API Key（免费）
1. 打开 https://platform.deepseek.com → 注册/登录
2. 右上角「API Keys」→ 创建 Key → 复制保存（形如 `sk-xxxx`）
3. 首次使用需先充值/领取额度（新用户通常有赠送额度）

---

## 1. 安装 Docker Desktop（不用 brew）
1. 浏览器打开 https://www.docker.com/products/docker-desktop/ → 下载 macOS 版 `.dmg`
2. 双击安装，启动 Docker Desktop，确认菜单栏出现鲸鱼图标且状态为 running
3. 终端验证：`docker --version` 有输出即可（首次启动可能要授权/输入密码）

---

## 2. 配置 Docker Hub 镜像加速（关键，否则拉不动镜像）
国内直连 Docker Hub 经常超时。在 Docker Desktop 里加一个国内镜像源：
1. Docker Desktop → Settings（齿轮）→ **Docker Engine**
2. 在配置 JSON 的 `registry-mirrors` 数组里加入镜像地址，例如：
   ```json
   {
     "registry-mirrors": [
       "https://docker.m.daocloud.io",
       "https://hub-mirror.c.163.com"
     ]
   }
   ```
   （二选一或都加；若某源失效可换阿里云个人加速器 https://cr.console.aliyun.com 获取专属地址）
3. 点 **Apply & Restart** 让配置生效

---

## 3. 填 .env
```bash
cd ai-agent-workbench
cp .env.example .env
```
用文本编辑器打开 `.env`，只改这一行（其余保持默认）：
```
DEEPSEEK_API_KEY=sk-你的真实key
```
> `embedding_provider` 保持默认的 `fake` 即可——这样不需要 OpenAI Key、也不需要下载模型，整条流水线（建库→入库→检索→对话）都能跑通。
> 想做「真·中文 RAG」再切 `openai`（需代理）或 `bge`（需下载权重，国内用 hf-mirror.com）。

---

## 4. 一键启动
```bash
bash scripts/run.sh
```
脚本会：构建镜像 → 起 PostgreSQL(pgvector) + Redis + API → 等就绪 → 初始化数据库 → 灌入退款政策演示知识库。

看到 `完成。浏览器打开 http://localhost:8000` 即成功。

---

## 5. 验证
- 浏览器打开 http://localhost:8000
- **右侧检索**：输入 `质量问题退货的运费谁承担`，应返回知识库片段
- **左侧对话**：输入 `根据知识库，退款多久到账？`，应流式返回答案（由 DeepSeek 生成）
- 答案气泡下方标注「本回答由供应商：deepseek」

命令行验证检索：
```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"质量问题退货的运费谁承担"}'
```

---

## 6. 常见问题
- **`docker: command not found`**：Docker Desktop 没装或没启动，回到第 1 步。
- **拉镜像卡在 `pulling` / timeout**：镜像加速没配或源失效，回到第 2 步换镜像源。
- **`pip install` 超时**：Dockerfile 已配置清华 PyPI 镜像；若仍慢，检查本机网络是否能访问 pypi.tuna.tsinghua.edu.cn。
- **对话报错「未配置任何 LLM 供应商」**：`.env` 没填 `DEEPSEEK_API_KEY`，回到第 3 步。
- **DeepSeek 返回 401**：Key 有误或额度用尽，去 platform.deepseek.com 核对。
- **Apple 芯片架构报错**：pgvector 镜像优先拉 arm64；若报错可显式指定平台，或在 docker-compose 的 postgres 服务加 `platform: linux/amd64`（用 Rosetta 模拟，首次较慢）。

---

## 7. 停止 / 清理
```bash
docker compose down            # 停止并保留数据卷
docker compose down -v         # 停止并删除数据卷（下次启动重新建库）
```
