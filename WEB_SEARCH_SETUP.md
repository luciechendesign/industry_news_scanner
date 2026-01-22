# 网络搜索功能使用说明

## 功能概述

现在系统支持两种搜索源：
1. **RSS 源**：从配置的RSS feeds中收集新闻（原有功能）
2. **网络搜索**：使用AI生成关键词，然后在网络上搜索相关新闻（新功能）

## 配置网络搜索API

### 自动配置（推荐）

**如果您使用 AI Builders**（已设置 `AI_BUILDER_TOKEN`），系统会自动：
- 使用 AI Builders 的搜索 API（基于 Tavily）
- 复用同一个 `AI_BUILDER_TOKEN`，无需额外配置
- 无需设置 `WEB_SEARCH_API_KEY` 或 `WEB_SEARCH_API_PROVIDER`

**如果您使用 Perplexity**（已设置 `AI_API_KEY` 且使用 Perplexity），系统会自动：
- 使用 Perplexity 的搜索功能
- 复用同一个 `AI_API_KEY`，无需额外配置

### 手动配置

如果需要使用其他搜索提供商，在 `.env` 文件中添加以下配置：

```bash
# 网络搜索API配置（可选，系统会自动检测）
WEB_SEARCH_API_PROVIDER=tavily  # 可选: tavily, perplexity, bing, ai-builders, custom
WEB_SEARCH_API_KEY=your_api_key_here  # 如果未设置，会尝试使用 AI_API_KEY
WEB_SEARCH_API_URL=  # 仅当使用custom provider时需要
WEB_SEARCH_MAX_RESULTS=10  # 每个关键词的最大搜索结果数（可选，默认10）
```

### 支持的搜索API提供商

1. **AI Builders** (自动检测，推荐)
   - 如果已设置 `AI_BUILDER_TOKEN`，系统会自动使用
   - 使用 Tavily 搜索（通过 AI Builders 代理）
   - 同一个 token 可用于 AI 对话和搜索
   - API文档: https://space.ai-builders.com/backend/openapi.json

2. **Tavily** (默认fallback)
   - 专为AI Agent设计的搜索API
   - 注册地址: https://tavily.com
   - 需要单独设置 `WEB_SEARCH_API_PROVIDER=tavily` 和 `WEB_SEARCH_API_KEY`

3. **Perplexity** (自动检测)
   - AI驱动的搜索API
   - 如果已设置 `AI_API_KEY` 且使用 Perplexity，系统会自动使用
   - 注册地址: https://www.perplexity.ai
   - 可以手动设置 `WEB_SEARCH_API_PROVIDER=perplexity`

4. **Bing Search API**
   - Microsoft Bing搜索API
   - 注册地址: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
   - 需要设置 `WEB_SEARCH_API_PROVIDER=bing` 和 `WEB_SEARCH_API_KEY`

5. **Custom API**
   - 自定义搜索API端点
   - 设置 `WEB_SEARCH_API_PROVIDER=custom`
   - 设置 `WEB_SEARCH_API_URL=your_api_endpoint`

## 使用方法

1. 启动后端服务器（参考 QUICK_START.md）
2. 打开前端页面
3. 在"搜索源"选项中选择：
   - **RSS 源**：使用RSS feeds收集新闻
   - **网络搜索**：使用AI生成关键词并搜索网络
4. 点击"Start Scan"按钮

## 工作原理

### RSS 搜索模式（原有功能）
- 从 `rss_feeds.json` 中读取RSS源
- 收集最近48小时内的新闻（可配置）
- 去重并转换为NewsItem格式

### 网络搜索模式（新功能）
1. **生成关键词**：AI根据 `background.md` 的战略目标和监控范围生成3-5个搜索关键词
2. **执行搜索**：对每个关键词执行网络搜索
3. **收集结果**：将搜索结果转换为NewsItem格式
4. **去重处理**：使用与RSS相同的去重逻辑
5. **AI分析**：与RSS模式一样，使用AI分析所有收集到的新闻

## 时间过滤

系统会自动过滤搜索结果，只保留最近30天内的内容：

- **默认时间窗口**：30天（可通过 `WEB_SEARCH_TIME_WINDOW_DAYS` 环境变量配置）
- **日期提取**：系统会从搜索结果描述和URL中提取发布日期
- **过滤规则**：
  - 如果找到明确的发布日期且超过时间窗口，会跳过该结果
  - 如果标题/描述中包含明显过时的年份（如2023年，当前是2025年），会跳过
  - 如果无法确定日期，会保留结果（搜索API通常已按时间排序）

**配置时间窗口**（可选）：
在 `.env` 文件中添加：
```bash
WEB_SEARCH_TIME_WINDOW_DAYS=30  # 默认30天，可调整为7、14、60等
```

## 注意事项

- **自动配置**：如果使用 AI Builders 或 Perplexity，系统会自动检测并使用相应的搜索API，无需额外配置
- **API密钥**：如果未设置 `WEB_SEARCH_API_KEY`，系统会尝试使用 `AI_API_KEY` 或 `AI_BUILDER_TOKEN`
- **时间过滤**：系统会自动过滤掉超过30天的旧内容，确保只返回最新信息
- 网络搜索可能比RSS搜索耗时更长
- 搜索结果的质量取决于使用的搜索API提供商
- AI生成的关键词基于 `background.md` 的内容，确保该文件是最新的

## 故障排除

### 网络搜索失败
- **如果使用 AI Builders**：检查 `AI_BUILDER_TOKEN` 是否正确设置
- **如果使用其他提供商**：检查 `WEB_SEARCH_API_KEY` 或 `AI_API_KEY` 是否正确
- 检查API提供商设置是否正确（系统会自动检测，通常无需手动设置）
- 查看后端日志了解详细错误信息

### 关键词生成失败
- 确保 `background.md` 文件存在且格式正确
- 检查AI API配置是否正确（`AI_API_KEY` 等）

