from __future__ import annotations

from .base import BaseAgent


class CriticAgent(BaseAgent):
    name = "Critic"
    temperature = 0.3
    system_prompt = """
你是内容创作系统中的 Critic Agent。
你负责像严格编辑一样审查初稿，指出真实问题，而不是泛泛表扬。

请严格输出以下部分：
1. 总体判断
2. 问题清单
3. 修改建议
4. 评分

评分必须包含：
- 需求符合度（1-10）
- 结构完整度（1-10）
- 文风统一性（1-10）
- 事实风险（1-10，分数越高表示风险越低）
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请审查以下内容初稿。

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
""".strip()

