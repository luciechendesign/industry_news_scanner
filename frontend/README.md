# Frontend - Industry News Scanner

## 文件说明

- `index.html` - 主页面，包含触发按钮和报告展示区域
- `styles.css` - 样式文件，现代化的UI设计
- `app.js` - 前端逻辑，处理API调用和UI交互

## 功能特性

1. **扫描触发**: 点击"Start Scan"按钮触发Two-Stage Scan工作流
2. **Loading状态**: 显示扫描进度和加载动画
3. **报告展示**: 
   - 按importance分组（High/Medium/Low）
   - 显示重要性统计
   - 每个条目显示标题、重要性、置信度、来源
4. **详细信息**: 点击条目可展开查看：
   - Why It Matters
   - Evidence
   - Recommended Actions
   - Second Order Impacts
   - Category
   - Dedupe Note
5. **JSON复制**: 一键复制完整JSON报告

## 使用方法

### 方法1: 通过FastAPI服务器访问

1. 启动后端服务器：
   ```bash
   uvicorn backend.main:app --reload
   ```

2. 访问前端：
   - 如果配置了静态文件服务，访问 http://localhost:8000
   - 或者直接打开 `index.html` 文件

### 方法2: 使用Python HTTP服务器

```bash
cd frontend
python3 -m http.server 8080
```

然后访问 http://localhost:8080

### 方法3: 直接打开HTML文件

直接在浏览器中打开 `frontend/index.html` 文件

**注意**: 方法2和3需要确保后端API在 http://localhost:8000 运行

## API配置

前端默认连接到 `http://localhost:8000`。如果需要修改API地址，编辑 `app.js` 中的 `API_BASE_URL` 常量。

