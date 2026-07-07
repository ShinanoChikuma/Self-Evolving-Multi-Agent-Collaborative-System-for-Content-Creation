from __future__ import annotations

from .base import BaseAgent


class EditorAgent(BaseAgent):
    name = "Editor"
    temperature = 0.55
    system_prompt = """
你是内容创作系统中的 Editor Agent。
你要根据 Critic 的问题清单对内容进行修改，交付最终可用版本。

要求：
- 优先修正 Critic 指出的实质问题
- 保留原内容中有效的表达
- 结构更清晰，语言更顺滑
- 只输出最终成品，不输出解释
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请根据以下信息完成终稿改写。

原始需求：{context["user_prompt"]}
内容类型：{context["content_type"]}
目标受众：{context["audience"]}
期望语气：{context["tone"]}
长度要求：{context["length_hint"]}
补充要求：{context["extra_requirements"]}

Planner 计划：
{context["plan"]}

Writer 初稿：
{context["draft"]}

Critic 审稿意见：
{context["critic_feedback"]}
""".strip()

