from __future__ import annotations

from .base import BaseAgent


class EvolutionAgent(BaseAgent):
    """Evolution Agent — 根据反馈总结策略，更新 prompt 或工作流。

    定期或在积累足够反馈后触发，分析反馈模式，生成进化建议：
    - 提示词优化：针对各 Agent 的 system_prompt 改进建议
    - 工作流调整：是否需要调整 Agent 顺序或增加步骤
    - 评分规则更新：Critic 的评分维度是否需要调整
    """

    name = "Evolution"
    temperature = 0.4
    system_prompt = """
你是内容创作系统中的 Evolution Agent。
你的职责是分析用户反馈数据，发现模式，提出系统进化策略。

请严格输出以下部分：
1. 反馈趋势分析（高分与低分案例的共同特征）
2. 提示词改进建议（针对 Planner/Writer/Critic/Editor 的具体修改）
3. 工作流调整建议（是否需要增删步骤或调整顺序）
4. 评分规则优化（Critic 的评分维度是否需要调整）
5. 模板优化建议（现有模板是否需要调整默认参数）

要求：
- 每项建议必须有数据支撑（引用具体案例）
- 改进建议必须可执行、可验证
- 优先级从高到低排序
""".strip()

    def build_user_prompt(self, context: dict[str, str]) -> str:
        return f"""
请分析以下反馈数据并生成进化建议。

系统当前状态：
{context.get("system_state", "未知")}

近期反馈汇总：
{context.get("feedback_summary", "暂无反馈")}

当前各 Agent 的 System Prompt：
- Planner: {context.get("planner_prompt", "")[:200]}
- Writer: {context.get("writer_prompt", "")[:200]}
- Critic: {context.get("critic_prompt", "")[:200]}
- Editor: {context.get("editor_prompt", "")[:200]}

用户记忆画像：
{context.get("memory_profile", "暂无")}

请输出系统进化建议。
""".strip()
