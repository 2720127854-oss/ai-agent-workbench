# 发布到 GitHub 实操指南（本机、无需 brew / 无需 gh）

> 适用场景：你的 Mac 没有 `brew`、没有 `gh`、没有 GitHub Desktop，且直连 GitHub 常被墙。
> **推荐路径（免梯子、已验证可用）：SSH over 443** —— 配置一次，之后 `git push` 走 `ssh.github.com:443` 通道。
> 备选：PAT + HTTPS（国内直连可能超时，需配梯子或多次重试）。

---

## ★ 推荐路径：SSH over 443（免梯子，已实测可用）

1. 生成密钥（无密码，回车到底）：
   ```bash
   ssh-keygen -t ed25519 -C "zhanrongxi-github" -f ~/.ssh/id_ed25519 -N ""
   ```
2. 写 SSH 配置（让 github.com 走 443 加密通道）：
   ```bash
   printf 'Host github.com\n  HostName ssh.github.com\n  Port 443\n  User git\n  IdentityFile ~/.ssh/id_ed25519\n' > ~/.ssh/config
   chmod 600 ~/.ssh/config ~/.ssh/id_ed25519
   ```
3. 把公钥告诉 GitHub：复制下面这行
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   浏览器打开 https://github.com/settings/ssh/new → Title 随便填 → Key 粘贴 → Add SSH key。
4. 切到 SSH 地址并推送：
   ```bash
   git remote set-url origin git@github.com:你的用户名/ai-agent-workbench.git
   git push -u origin main
   ```
   > 国内会间歇性超时，多跑几次即可（"Operation timed out" 就重来）。

---

## 一、在哪里输入命令
打开 Mac 的「终端」App：
- 按 `Cmd + 空格` → 输入「终端」→ 回车。
- 把下面每一段命令**单独粘贴、回车**执行，不要一次性全粘。

---

## 二、在 GitHub 网页新建一个空仓库（关键：不要勾 README）
1. 浏览器打开 https://github.com → 右上角 `+` → **New repository**。
2. Repository name 填：`ai-agent-workbench`
3. 选 **Public**。
4. **不要**勾选 "Add a README file" / "Add .gitignore" / "Choose a license"（项目里已经有了，勾了反而推送冲突）。
5. 点 **Create repository**。
6. 创建后会看到一行地址，形如：
   `https://github.com/你的用户名/ai-agent-workbench.git`
   复制它备用。

---

## 三、生成个人访问令牌（PAT）
1. 浏览器打开 https://github.com/settings/tokens
2. 点 **Generate new token** → **Generate new token (classic)**。
3. Note 填：`workbench-publish`
4. Expiration：选 `30 days`（或 No expiration）。
5. 在 scopes 里**勾选 `repo`**（点一下全选该分组）。
6. 拉到底点 **Generate token**。
7. 页面会显示一长串 `ghp_xxx...` —— **立刻复制保存**，它只显示这一次。

---

## 四、终端执行推送（把「你的用户名」和「令牌」换成你自己的）
```bash
cd /Users/zhanrongxi/WorkBuddy/2026-10-27-23-09-15/ai-agent-workbench

git remote add origin https://github.com/你的GitHub用户名/ai-agent-workbench.git

git branch -M main

git push -u origin main
```
- 提示 `Username for 'https://github.com'`：填你的 GitHub 用户名，回车。
- 提示 `Password for 'https://github.com'`：**粘贴第三步复制的 PAT**（粘贴时屏幕不显示字符，属正常），回车。
- 看到 `main -> main` 或 `Writing objects ... done` 即成功。

---

## 五、成功之后
把仓库地址（形如 `https://github.com/你的用户名/ai-agent-workbench`）发给助手，
助手会把链接填进：
- `作品集_多模型Agent对话工作台.html`
- `湛荣郗_AI应用开发工程师_简历.docx`

---

## 手机可以上传吗？（结论：不推荐）
- 项目文件目前在 **Mac** 上，不在手机里；推送需要"同时有文件 + 能连 GitHub"的机器。
- GitHub 手机 App 只能看代码/处理 Issue/PR，不能把本地文件夹批量建仓库。
- 手机浏览器 github.com 的"上传文件"是拖拽，手机无文件夹拖拽能力，且一次只能传零散文件，无法处理 39 文件 + 目录结构。
- 即便把文件传到手机，iOS/Android 也没有好用的 git 客户端能一键 commit+push 整个项目。
- **所以请在 Mac 上操作**，下面两条 Mac 路径任选。

## 路径 A（推荐，最快，零下载）：终端 4 条命令
见上方「二~四」步骤，用 PAT + 原生 git 推送，约 2 分钟。

## 路径 B（纯图形界面，需下载 dmg，不用 brew）
1. 浏览器打开 https://desktop.github.com → 下载 `.dmg` 直接安装（官网正常下载，非 brew）。
2. 打开 GitHub Desktop → Sign in 登录 GitHub。
3. File → Add Local Repository → 选择 `ai-agent-workbench` 文件夹。
4. 点 **Publish repository** → Name 填 `ai-agent-workbench`、勾 Public → Publish。

---

## 备选方案：想用 gh 但不想装 brew（不推荐，步骤更多）
直接下载官方预编译二进制，免 brew：
```bash
cd /tmp
curl -L -o gh.tar.gz https://github.com/cli/cli/releases/latest/download/gh_$( \
  curl -s https://api.github.com/repos/cli/cli/releases/latest | grep -oE 'tag_name": *"v[0-9.]+' | grep -oE '[0-9.]+' \
)_macOS_amd64.tar.gz
tar -xzf gh.tar.gz
sudo mv gh_*/bin/gh /usr/local/bin/gh
gh auth login      # 浏览器授权
bash scripts/publish.sh
```
