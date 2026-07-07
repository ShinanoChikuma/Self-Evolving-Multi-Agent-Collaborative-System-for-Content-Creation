from __future__ import annotations

from .base import BaseAgent


class MemoryAgent(BaseAgent):
    """Memory Agent — 记录用户偏好、风格记忆，为创作上下文注入历史经验。

    在每次创作前运行，读取 memory.json 中积累的用户画像和成功案例，
    生成一段结构化的"记忆上下文"供 Planner 和 Writer 参考。
    """

    name = "Memory"
    temperature = 0.3
    system_prompt = """
你是内容创作系统中的 Memory Agent。
你的职责是基于用户历史偏好与成功案例，提取对本次创作最有价值的参考信息。

请严格输出以下部分：
1. 用户风格偏好总结（语气、结构、长度倾向）
2. 与本次任务类型相关的高分案例要点
3. 需要继承的写作习惯与约束
4. 需要避免的问题（基于历史低分案例）

只输出对本次创作有实际指导价值的信息，不要泛泛总结。
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请基于以下信息提取本次创作的记忆参考。

当前任务：
- 内容类型：{context.get("content_type", "未知")}
- 核心需求：{context.get("user_prompt", "未知")}
- 目标受众：{context.get("audience", "未指定")}
- 期望语气：{context.get("tone", "未指定")}
- 长度要求：{context.get("length_hint", "未知")}

用户历史记忆：
{context.get("memory_context", "暂无历史数据")}

近期成功案例：
{context.get("successful_cases", "暂无")}

请输出对本次创作最有价值的记忆参考。
""".strip()
