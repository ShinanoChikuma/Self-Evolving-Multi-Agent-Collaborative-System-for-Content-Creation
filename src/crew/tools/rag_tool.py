"""将 RAG 检索器封装为 CrewAI Tool —— Agent 可自主调用检索历史案例。"""

from __future__ import annotations

from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class RAGSearchInput(BaseModel):
    """RAG 检索参数"""
    query: str = Field(description="搜索查询，输入当前创作需求的核心关键词或主题")
    content_type: str = Field(default="", description="按内容类型过滤，如'短视频脚本'、'公众号文章'")


class RAGTool(BaseTool):
    """搜索历史创作案例，找到与当前需求最相似的成功作品作为参考。"""

    name: str = "历史案例检索"
    description: str = (
        "搜索历史创作案例数据库，找到与当前需求最相似的成功作品。"
        "当需要参考过往成功经验、了解类似需求的执行方式时使用此工具。"
    )
    args_schema: Type[BaseModel] = RAGSearchInput

    # 外部注入的 Retriever 实例
    retriever: Any = Field(default=None, exclude=True)

    def __init__(self, retriever: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if retriever is not None:
            self.retriever = retriever

    def _run(self, query: str, content_type: str = "") -> str:
        if self.retriever is None:
            return "历史案例检索暂不可用（索引未初始化）"
        try:
            result = self.retriever.retrieve_context(
                query=query,
                content_type=content_type,
                top_k=3,
            )
            return result
        except Exception as exc:
            return f"检索失败：{exc}"
