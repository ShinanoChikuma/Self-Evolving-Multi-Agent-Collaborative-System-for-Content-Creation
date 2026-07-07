"""全网搜索 Tool —— 通过 DuckDuckGo 进行免费网页搜索。"""

from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """搜索参数"""
    query: str = Field(description="搜索查询词，如'AI耳机 2025 评测'、'短视频脚本 写作技巧'")


class WebSearchTool(BaseTool):
    """在互联网上搜索最新信息、文章、讨论等。免费，无需 API Key。"""

    name: str = "全网搜索"
    description: str = (
        "在互联网上搜索最新信息。适合查找实时资讯、产品评测、热点话题、"
        "行业趋势等。返回搜索结果的标题和摘要。使用中文关键词搜索效果更好。"
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS
            results = list(DDGS().text(query, max_results=5))
            if not results:
                return "未找到相关搜索结果，请尝试调整搜索词。"
            lines = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                body = r.get("body", "")[:200]
                href = r.get("href", "")
                lines.append(f"[{i}] {title}\n    {body}\n    {href}")
            return "\n\n".join(lines)
        except ImportError:
            return "搜索功能不可用：缺少 duckduckgo_search 库。"
        except Exception as exc:
            return f"搜索失败：{exc}"
