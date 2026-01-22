# 快速启动指南

## 问题：uvicorn 命令未找到

如果遇到 `uvicorn: command not found` 错误，这是因为 uvicorn 的可执行文件不在 PATH 中。

## ✅ 解决方案：使用 python3 -m uvicorn

### 方法1：使用启动脚本（最简单）

```bash
cd /Users/luqianchen/Documents/Industry_news
./start_server.sh
```

### 方法2：直接使用 python3 -m uvicorn

```bash
cd /Users/luqianchen/Documents/Industry_news
python3 -m uvicorn backend.main:app --reload
```

### 方法3：从backend目录启动

```bash
cd /Users/luqianchen/Documents/Industry_news/backend
python3 -m uvicorn main:app --reload
```

## 完整启动流程

### 1. 确保依赖已安装

```bash
cd /Users/luqianchen/Documents/Industry_news/backend
pip3 install -r requirements.txt
```

### 2. 启动后端服务器

**终端窗口1**：

```bash
cd /Users/luqianchen/Documents/Industry_news
python3 -m uvicorn backend.main:app --reload
```

看到以下输出表示启动成功：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. 打开前端

**方法A：直接打开HTML文件**（推荐）

在Finder中找到 `frontend/index.html` 并双击打开，或在终端：

```bash
open frontend/index.html
```

**方法B：使用HTTP服务器**

**终端窗口2**：

```bash
cd /Users/luqianchen/Documents/Industry_news/frontend
python3 -m http.server 8080
```

然后访问：http://localhost:8080

### 4. 开始使用

1. 在浏览器中打开前端页面
2. 点击 "Start Scan" 按钮
3. 等待扫描完成（可能需要5-10分钟）
4. 查看报告结果

## 验证安装

运行以下命令验证一切正常：

```bash
# 检查Python版本
python3 --version

# 检查uvicorn是否可用
python3 -m uvicorn --version

# 检查FastAPI是否安装
python3 -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
```

## 常见问题

### Q: 为什么不能直接用 `uvicorn` 命令？

A: 因为使用了 `pip3 install --user` 安装，可执行文件在用户目录中，不在系统PATH中。使用 `python3 -m uvicorn` 可以避免这个问题。

### Q: 如何让 `uvicorn` 命令直接可用？

A: 将用户bin目录添加到PATH：

```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

然后重新加载：
```bash
source ~/.zshrc
```

但推荐使用 `python3 -m uvicorn`，更可靠。

### Q: 端口8000被占用怎么办？

A: 使用其他端口：

```bash
python3 -m uvicorn backend.main:app --reload --port 8001
```

然后修改 `frontend/app.js` 中的 `API_BASE_URL` 为 `http://localhost:8001`

## 测试API

服务器启动后，可以测试：

```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

## 停止服务器

在运行服务器的终端窗口按 `Ctrl+C` 停止服务器。

