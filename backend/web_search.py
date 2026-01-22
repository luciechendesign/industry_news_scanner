"""Web search module supporting multiple search API providers."""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
from .config import (
    WEB_SEARCH_API_PROVIDER,
    WEB_SEARCH_API_KEY,
    WEB_SEARCH_API_URL,
    WEB_SEARCH_MAX_RESULTS,
    AI_BUILDER_TOKEN,
    AI_API_KEY
)


class WebSearchClient:
    """Unified web search client supporting multiple providers."""
    
    def __init__(self):
        self.provider = WEB_SEARCH_API_PROVIDER
        # Use AI_BUILDER_TOKEN if available and using ai-builders provider
        if self.provider == "ai-builders" and AI_BUILDER_TOKEN:
            self.api_key = AI_BUILDER_TOKEN
        else:
            self.api_key = WEB_SEARCH_API_KEY
        self.api_url = WEB_SEARCH_API_URL
        self.max_results = WEB_SEARCH_MAX_RESULTS
        
        if not self.api_key:
            raise ValueError(
                "WEB_SEARCH_API_KEY or AI_API_KEY/AI_BUILDER_TOKEN must be set in .env file. "
                "If using AI Builders, the same token works for both AI and search."
            )
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search for a given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of search results, each containing:
            - title: Result title
            - url: Result URL
            - description: Result snippet/description
            - source: Source website name
        """
        if self.provider == "tavily":
            return self._search_tavily(query)
        elif self.provider == "perplexity":
            return self._search_perplexity(query)
        elif self.provider == "bing":
            return self._search_bing(query)
        elif self.provider == "ai-builders":
            return self._search_ai_builders(query)
        elif self.provider == "custom":
            return self._search_custom(query)
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
    
    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        url = "https://api.tavily.com/search"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": self.max_results
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("content", ""),
                        "source": self._extract_domain(item.get("url", ""))
                    })
                
                return results
        except Exception as e:
            print(f"Tavily search error: {e}")
            raise
    
    def _search_perplexity(self, query: str) -> List[Dict[str, Any]]:
        """Search using Perplexity API."""
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that searches the web and returns structured results."
                },
                {
                    "role": "user",
                    "content": f"Search for recent news about: {query}. Return a list of relevant articles with titles, URLs, and summaries."
                }
            ],
            "return_citations": True
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Perplexity returns citations in the response
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                citations = data.get("citations", [])
                
                results = []
                for citation in citations[:self.max_results]:
                    results.append({
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                        "description": citation.get("snippet", content[:200]),
                        "source": self._extract_domain(citation.get("url", ""))
                    })
                
                return results
        except Exception as e:
            print(f"Perplexity search error: {e}")
            raise
    
    def _search_ai_builders(self, query: str) -> List[Dict[str, Any]]:
        """Search using AI Builders Tavily search API."""
        url = "https://space.ai-builders.com/backend/v1/search/"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "keywords": [query],
            "max_results": self.max_results
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                results = []
                # AI Builders returns results in queries array
                for query_result in data.get("queries", []):
                    tavily_response = query_result.get("response", {})
                    for item in tavily_response.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "description": item.get("content", ""),
                            "source": self._extract_domain(item.get("url", ""))
                        })
                
                return results
        except Exception as e:
            print(f"AI Builders search error: {e}")
            raise
    
    def _search_bing(self, query: str) -> List[Dict[str, Any]]:
        """Search using Bing Search API."""
        if not self.api_url:
            url = "https://api.bing.microsoft.com/v7.0/search"
        else:
            url = self.api_url
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": self.max_results,
            "textDecorations": False,
            "textFormat": "Raw"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("webPages", {}).get("value", []):
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("url", ""),
                        "description": item.get("snippet", ""),
                        "source": self._extract_domain(item.get("url", ""))
                    })
                
                return results
        except Exception as e:
            print(f"Bing search error: {e}")
            raise
    
    def _search_custom(self, query: str) -> List[Dict[str, Any]]:
        """Search using custom API endpoint."""
        if not self.api_url:
            raise ValueError("WEB_SEARCH_API_URL must be set for custom provider")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Try OpenAI-compatible format first
        payload = {
            "query": query,
            "max_results": self.max_results
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Try to parse common response formats
                if isinstance(data, list):
                    results = data
                elif isinstance(data, dict):
                    results = data.get("results", data.get("items", data.get("data", [])))
                else:
                    results = []
                
                # Normalize results
                normalized_results = []
                for item in results[:self.max_results]:
                    if isinstance(item, dict):
                        normalized_results.append({
                            "title": item.get("title", item.get("name", "")),
                            "url": item.get("url", item.get("link", "")),
                            "description": item.get("description", item.get("snippet", item.get("content", ""))),
                            "source": self._extract_domain(item.get("url", item.get("link", "")))
                        })
                
                return normalized_results
        except Exception as e:
            print(f"Custom search error: {e}")
            raise
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        if not url:
            return "Unknown"
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "Unknown"

