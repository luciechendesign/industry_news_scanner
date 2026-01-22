"""AI API client supporting multiple providers."""
import json
import re
import httpx
from httpx import Timeout, Limits
from typing import Dict, Optional, Any, List
from .config import AI_API_KEY, AI_API_URL, AI_PROVIDER, AI_MODEL


class AIClient:
    """Unified AI API client supporting OpenAI, Anthropic, and custom APIs."""
    
    def __init__(self):
        self.api_key = AI_API_KEY
        self.api_url = AI_API_URL
        self.provider = AI_PROVIDER
        self.model = AI_MODEL
        
        if not self.api_key:
            raise ValueError("AI_API_KEY or AI_BUILDER_TOKEN must be set in .env file")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response with robust error handling.
        Attempts to fix common JSON errors and extract valid JSON.
        """
        original_text = response_text
        
        # Step 1: Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        # Step 2: Try direct JSON parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Step 3: Try to extract JSON object by matching braces
        json_start = response_text.find('{')
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found", original_text, 0)
        
        # Extract JSON object by matching braces
        brace_count = 0
        json_end = -1
        for i in range(json_start, len(response_text)):
            char = response_text[i]
            # Skip characters inside strings
            if char == '"' and (i == 0 or response_text[i-1] != '\\'):
                # Find the end of this string
                j = i + 1
                while j < len(response_text):
                    if response_text[j] == '"' and response_text[j-1] != '\\':
                        i = j
                        break
                    j += 1
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end > json_start:
            json_text = response_text[json_start:json_end]
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                # Try to fix common issues in the extracted JSON
                json_text = self._fix_json_common_issues(json_text)
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass
        
        # Step 4: Last resort - try to fix and parse the full text
        fixed_text = self._fix_json_common_issues(response_text[json_start:])
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError as e:
            # If all else fails, raise with helpful error message
            print(f"Failed to parse JSON after all attempts. Error: {e}")
            print(f"Response text (first 1000 chars): {original_text[:1000]}")
            raise
    
    def _fix_json_common_issues(self, text: str) -> str:
        """Fix common JSON issues like unescaped quotes and incomplete strings."""
        # Fix 1: Escape unescaped quotes in string values
        # Pattern: find "key": "value with "quote" here"
        # We need to be careful not to break valid JSON
        
        # Fix 2: Remove trailing incomplete strings
        # Find the last complete property and remove anything after
        
        lines = text.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check if this line has an incomplete string (starts with " but doesn't end properly)
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                continue
            
            # Check for incomplete string values
            # Pattern: "key": "incomplete string
            if ':' in stripped and stripped.count('"') % 2 != 0:
                # Odd number of quotes - likely incomplete
                # Try to complete it by finding where it should end
                colon_pos = stripped.find(':')
                if colon_pos != -1:
                    key_part = stripped[:colon_pos].strip()
                    value_part = stripped[colon_pos+1:].strip()
                    
                    if value_part.startswith('"') and not value_part.endswith('"'):
                        # Incomplete string - try to close it at end of line or next line
                        # For now, just close it
                        if not value_part.endswith('",') and not value_part.endswith(','):
                            value_part = value_part.rstrip(',') + '",'
                        else:
                            value_part = value_part.rstrip(',') + '"'
                    
                    fixed_lines.append('  ' + key_part + ': ' + value_part)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        result = '\n'.join(fixed_lines)
        
        # Ensure JSON is properly closed
        open_braces = result.count('{') - result.count('}')
        open_brackets = result.count('[') - result.count(']')
        
        if open_braces > 0:
            result = result.rstrip() + '\n' + '}' * open_braces
        if open_brackets > 0:
            result = result.rstrip() + ']' * open_brackets
        
        return result
    
    def _call_openai_api(self, messages: list, temperature: float = 0.7) -> str:
        """Call OpenAI-compatible API."""
        url = self.api_url if self.api_url else "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"}  # Request JSON response
        }
        
        # Use more robust timeout and connection settings
        timeout = Timeout(60.0, connect=10.0)
        limits = Limits(max_keepalive_connections=5, max_connections=10)
        
        with httpx.Client(timeout=timeout, limits=limits, verify=True) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _call_anthropic_api(self, messages: list, temperature: float = 0.7) -> str:
        """Call Anthropic API."""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Convert messages format for Anthropic
        system_message = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": user_messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        # Use more robust timeout and connection settings
        timeout = Timeout(60.0, connect=10.0)
        limits = Limits(max_keepalive_connections=5, max_connections=10)
        
        with httpx.Client(timeout=timeout, limits=limits, verify=True) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
    
    def _call_custom_api(self, messages: list, temperature: float = 0.7) -> str:
        """Call custom API (e.g., AI Builders)."""
        if not self.api_url:
            raise ValueError("API_URL must be set for custom API provider")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Check if API uses OpenAI-compatible format (chat/completions endpoint)
        if "/chat/completions" in self.api_url or "/v1/chat" in self.api_url:
            # OpenAI-compatible format
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"}
            }
        else:
            # Legacy format: convert messages to single prompt
            prompt = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": 4096
            }
        
        # Use more robust timeout and connection settings
        timeout = Timeout(60.0, connect=10.0)
        limits = Limits(max_keepalive_connections=5, max_connections=10)
        
        with httpx.Client(timeout=timeout, limits=limits, verify=True) as client:
            response = client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Handle OpenAI-compatible response format
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0]["message"]["content"]
            
            # Handle different response formats
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                # Try common response fields
                return result.get("text") or result.get("content") or result.get("response") or str(result)
            else:
                return str(result)
    
    def analyze_news_item(self, news_item: Dict[str, Any], background_context: str) -> Dict[str, Any]:
        """
        Analyze a single news item using AI.
        
        Args:
            news_item: NewsItem as dictionary
            background_context: Content of background.md
            
        Returns:
            Analyzed report item as dictionary
        """
        # Build prompt
        prompt = self._build_analysis_prompt(news_item, background_context)
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert strategic analyst. Analyze news items based on strategic context and return ONLY valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call appropriate API
        try:
            # Determine provider based on config
            if self.provider == "anthropic":
                response_text = self._call_anthropic_api(messages)
            elif self.provider == "custom" or self.api_url:
                # Custom API or OpenAI-compatible custom endpoint
                response_text = self._call_custom_api(messages)
            else:  # default to OpenAI
                response_text = self._call_openai_api(messages)
        except Exception as api_err:
            raise
        
        # Parse JSON response with robust error handling
        try:
            result = self._parse_json_response(response_text)
        except Exception as json_err:
            raise
        
        # Ensure all required fields are present
        result["title"] = news_item.get("title", "")
        result["source"] = news_item.get("source", "")
        result["url"] = news_item.get("url", "")
        
        return result
    
    def _build_analysis_prompt(self, news_item: Dict[str, Any], background_context: str) -> str:
        """Build the analysis prompt for AI."""
        title = news_item.get("title", "")
        description = news_item.get("description", "") or news_item.get("content", "")
        url = news_item.get("url", "")
        source = news_item.get("source", "")
        
        prompt = f"""基于以下战略背景分析这条新闻。

重要：所有分析内容必须使用中文（简体中文）输出，包括：
- why_it_matters 数组中的每个原因
- evidence 字段的内容
- second_order_impacts 字段的内容
- recommended_actions 数组中的每个行动
- dedupe_note 字段的内容

只有以下内容保持英文：
- JSON 字段名（importance, confidence 等）
- importance 的值（"high", "medium", "low"）
- category 的值（"平台规则" | "卖家玩法" | "红人生态" | "合规" | "工具链" | null）
- URL 和技术术语

STRATEGIC CONTEXT (from background.md):
{background_context}

NEWS ITEM TO ANALYZE:
Title: {title}
Source: {source}
URL: {url}
Description: {description[:1000] if description else "No description available"}

基于以上战略背景，分析这条新闻并提供结构化 JSON 响应，包含以下字段：

{{
  "importance": "high" | "medium" | "low",
  "confidence": 0.0-1.0,
  "why_it_matters": ["原因1", "原因2", ...],  // 2-5个原因，必须对应到 Goal 1/2/3（使用中文）
  "evidence": "关键事实和来源信息",  // 使用中文
  "second_order_impacts": "可能的二阶影响（如果有）",  // 使用中文
  "recommended_actions": ["行动1", "行动2", ...],  // 1-3个具体行动（使用中文）
  "dedupe_note": "是否与近期事件重复，或新增信息",  // 使用中文
  "category": "平台规则" | "卖家玩法" | "红人生态" | "合规" | "工具链" | null
}}

重要性判定标准（来自 background.md 第3节）：
- HIGH（高）：满足以下任意一条：未来7-30天策略影响、Amazon/平台规则变化、红人生态规则变化、竞品/关键工具重大动作、合规/法律重大变化、新模式/新渠道快速被采用
- MEDIUM（中）：相关但不确定/不紧急
- LOW（低）：泛行业内容、无明确关联、无影响路径

why_it_matters 中的原因应明确对应到：
- Goal 1（行业洞察建立）：说明如何帮助建立行业地图或判断框架
- Goal 2（产品与竞争）：说明如何影响产品决策或竞争策略
- Goal 3（关键风险）：说明如何帮助避免风险或识别威胁

只返回 JSON 对象，不要添加任何其他文本或解释。"""

        return prompt
    
    def generate_search_keywords(self, background_context: str) -> List[str]:
        """
        Generate search keywords based on strategic context from background.md.
        
        Args:
            background_context: Content of background.md
            
        Returns:
            List of search keyword strings (3-5 keywords)
        """
        prompt = self._build_keywords_prompt(background_context)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert strategic analyst. Generate search keywords based on strategic context and return ONLY valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            # Call appropriate API
            if self.provider == "anthropic":
                response_text = self._call_anthropic_api(messages, temperature=0.7)
            elif self.provider == "custom" or self.api_url:
                response_text = self._call_custom_api(messages, temperature=0.7)
            else:  # default to OpenAI
                response_text = self._call_openai_api(messages, temperature=0.7)
            
            # Parse JSON response
            result = self._parse_json_response(response_text)
            
            # Extract keywords
            keywords = result.get("keywords", [])
            if isinstance(keywords, list) and len(keywords) > 0:
                # Ensure we return strings
                return [str(k) for k in keywords[:10]]  # Max 10 keywords
            else:
                # Fallback: return default keywords (expanded list)
                return [
                    "Amazon seller policy changes 2025",
                    "Amazon influencer program updates",
                    "influencer marketing trends 2025",
                    "e-commerce platform rules 2025",
                    "FTC influencer disclosure rules",
                    "Agentio funding news",
                    "Aha influencer tool updates",
                    "Amazon seller compliance 2025"
                ]
                
        except Exception as e:
            print(f"Error generating search keywords: {e}")
            # Fallback keywords (expanded list)
            return [
                "Amazon seller policy changes 2025",
                "Amazon influencer program updates",
                "influencer marketing trends 2025",
                "e-commerce platform rules 2025",
                "FTC influencer disclosure rules",
                "Agentio funding news",
                "Aha influencer tool updates",
                "Amazon seller compliance 2025"
            ]
    
    def _build_keywords_prompt(self, background_context: str) -> str:
        """Build the prompt for generating search keywords."""
        from datetime import datetime
        current_year = datetime.now().year
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        prompt = f"""基于以下战略背景生成5-8个搜索关键词。

重要：今天是{current_date}。当前年份是{current_year}。在关键词中包含时间限制，确保只搜索最近30天的新闻。使用{current_year}而不是2024或其他过去的年份。

STRATEGIC CONTEXT (from background.md):
{background_context}

生成与以下内容对齐的搜索关键词：
1. 战略目标（Priority 1-3）
2. 监控范围（平台、政策、竞争对手跟踪等）
3. 重要性标准（什么使新闻具有高重要性）

每个关键词应该：
- 包含时间限制，例如："最近30天"、"2025年1月"等
- 足够具体以找到相关新闻
- 足够广泛以捕获重要发展
- 专注于最近的发展（最近7-30天）
- 使用{current_year}当提到日期时

示例关键词格式：
- "Amazon seller policy changes {current_year}"
- "influencer marketing news January {current_year}"
- "Agentio funding news last 30 days"

只返回JSON对象，结构如下：
{{
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5", "关键词6", "关键词7", "关键词8"],
  "reasoning": "选择这些关键词的简要说明"
}}

只返回JSON对象，不要添加其他文本。"""

        return prompt

