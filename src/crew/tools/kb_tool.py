"""将知识库检索封装为 CrewAI Tool。"""

from __future__ import annotations

from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class KBSearchInput(BaseModel):
    """知识库检索参数"""
    keyword: str = Field(description="搜索关键词，如'品牌文案'、'角色设定'、'小说开头'")


class KBTool(BaseTool):
    """搜索知识库中的参考条目和领域知识。"""

    name: str = "知识库检索"
    description: str = (
        "搜索知识库中的参考条目和领域知识。"
        "当需要查询特定领域的专业知识、模板参考、最佳实践时使用此工具。"
    )
    args_schema: Type[BaseModel] = KBSearchInput

    db: Any = Field(default=None, exclude=True)

    def __init__(self, db: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if db is not None:
            self.db = db

    def _run(self, keyword: str) -> str:
        if self.db is None:
            return "知识库暂不可用"
        try:
            entries = self.db.search_knowledge(keyword)
            if not entries:
                return "暂无相关知识库条目"
            return "\n".join(
                f"[{e.get('title', '')}] {e.get('content', '')[:300]}"
                for e in entries[:3]
            )
        except Exception as exc:
            return f"知识库检索失败：{exc}"
