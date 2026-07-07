"""将用户偏好记忆查询封装为 CrewAI Tool。"""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool


class MemoryTool(BaseTool):
    """查询用户的历史偏好：偏好的语气、擅长的内容类型、历史高分案例等。"""

    name: str = "用户偏好记忆"
    description: str = (
        "查询用户的历史创作偏好和成功模式，包括：偏好的语气风格、"
        "擅长的内容类型、历史高分案例预览。"
        "当需要了解用户喜好、个性化调整创作策略时使用此工具。"
    )

    db: Any = None

    def __init__(self, db: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if db is not None:
            self.db = db

    def _run(self, query: str = "") -> str:
        """查询用户偏好记忆。query 参数可指定内容类型过滤。"""
        if self.db is None:
            return "用户记忆暂不可用"
        try:
            result = self.db.get_memory_context(content_type=query)
            return result if result else "暂无历史记忆数据"
        except Exception as exc:
            return f"记忆查询失败：{exc}"
