from __future__ import annotations

from .base import BaseAgent


class WriterAgent(BaseAgent):
    name = "Writer"
    temperature = 0.85
    system_prompt = """
你是内容创作系统中的 Writer Agent。
你的任务是根据 Planner 的计划直接写出高质量初稿。

要求：
- 必须严格贴合用户需求
- 结构完整
- 语言自然，不要写成提示词回答风格
- 直接输出内容成品，不要额外解释
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请根据以下信息撰写初稿。

内容类型：{context["content_type"]}
核心需求：{context["user_prompt"]}
目标受众：{context["audience"]}
期望语气：{context["tone"]}
长度要求：{context["length_hint"]}
补充要求：{context["extra_requirements"]}

Planner 计划：
{context["plan"]}
""".strip()

