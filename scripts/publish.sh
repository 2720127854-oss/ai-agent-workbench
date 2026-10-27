#!/usr/bin/env bash
# 一键发布到 GitHub（解决「沙箱无凭据」：在你本机、已登录 gh 后运行）
# 用法：
#   1) 安装并登录： brew install gh && gh auth login   （浏览器授权，无需复制 token）
#   2) bash scripts/publish.sh
set -e
cd "$(dirname "$0")/.."

git add -A
git commit -m "chore: 发布前同步" || echo "（无新改动，跳过提交）"

if command -v gh >/dev/null 2>&1; then
  echo ">> 使用 gh 创建并推送仓库 ai-agent-workbench ..."
  gh repo create ai-agent-workbench --public --source=. --remote=origin --push
else
  echo "未检测到 gh，二选一："
  echo "  A) 安装并登录： brew install gh && gh auth login，然后重跑本脚本"
  echo "  B) 手动推送："
  echo "     git remote add origin https://github.com/<你的用户名>/ai-agent-workbench.git"
  echo "     git branch -M main && git push -u origin main"
fi
