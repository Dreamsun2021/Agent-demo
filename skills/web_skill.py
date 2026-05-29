# skills/web_skill.py
import json
import requests
from bs4 import BeautifulSoup

def search_web(query: str) -> str:
    """使用 Bing 进行通用网页搜索"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        url = f"https://www.bing.com/search?q={query}"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("li.b_algo")
        if not items:
            return f"未找到关于 '{query}' 的信息。"
        formatted = []
        for item in items[:5]:
            title_elem = item.select_one("h2 a")
            snippet_elem = item.select_one(".b_caption p")
            formatted.append({
                "title": title_elem.text if title_elem else "无标题",
                "url": title_elem["href"] if title_elem else "",
                "snippet": snippet_elem.text if snippet_elem else "无摘要"
            })
        return json.dumps(formatted, ensure_ascii=False)
    except Exception as e:
        return f"搜索失败：{str(e)}"

# 工具描述列表
WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "通用网络搜索工具，可用于查询任何实时信息、新闻、百科等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，例如'今天天气'"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# 函数映射
WEB_FUNCTIONS = {
    "search_web": search_web
}