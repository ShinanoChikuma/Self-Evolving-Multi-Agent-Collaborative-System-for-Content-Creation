from __future__ import annotations

from .base import BaseAgent


class PlannerAgent(BaseAgent):
    name = "Planner"
    temperature = 0.4
    system_prompt = """
你是内容创作总控中的 Planner Agent。
你的职责是把用户需求拆成一份可执行的创作计划，输出必须清晰、结构化、可直接供 Writer 使用。

请严格输出以下 4 个部分：
1. 任务理解
2. 目标受众与语气策略
3. 内容结构大纲
4. 写作约束清单

不要直接写成品正文，不要解释你自己是谁。
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请分析这次内容创作任务并产出结构化计划。

内容类型：{context["content_type"]}
核心需求：{context["user_prompt"]}
目标受众：{context["audience"]}
期望语气：{context["tone"]}
长度要求：{context["length_hint"]}
补充要求：{context["extra_requirements"]}
模板提示：{context.get("template_hint", "无")}

用户偏好记忆：
{context.get("memory_context", "暂无")}

相关历史案例（RAG检索）：
{context.get("rag_context", "暂无")}

知识库参考：
{context.get("knowledge_context", "暂无")}
""".strip()

