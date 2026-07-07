"""CrewAI 内容创作编排器 —— 替代原有的 ContentOrchestrator。

提供两个主要 Crew：
1. ContentCrew: Planner → Writer → Critic → Editor 串行流水线
2. EvolutionCrew: 独立的反馈分析与进化建议
"""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import yaml
from crewai import Crew, Process

from src.db import Database, utc_now
from src.rag import Retriever

from .agents import create_agents
from .tasks import create_content_tasks, create_evolution_task
from .tools import KBTool, MemoryTool, RAGTool
from .tools import WebSearchTool, WebReadTool, YouTubeTool, GitHubTool


class ContentCrew:
    """CrewAI 封装的内容创作流水线。

    保持与原有 ContentOrchestrator 兼容的接口（create_content / iterate_content /
    trigger_evolution），内部全部改为 CrewAI 驱动。
    """

    def __init__(self, db: Database, retriever: Retriever) -> None:
        self.db = db
        self.retriever = retriever

        # ── 封装 Tools ──────────────────────────────
        self.rag_tool = RAGTool(retriever=retriever)
        self.kb_tool = KBTool(db=db)
        self.memory_tool = MemoryTool(db=db)
        self.web_search_tool = WebSearchTool()
        self.web_read_tool = WebReadTool()
        self.youtube_tool = YouTubeTool()
        self.github_tool = GitHubTool()
        tools = [
            self.rag_tool, self.kb_tool, self.memory_tool,
            self.web_search_tool, self.web_read_tool,
            self.youtube_tool, self.github_tool,
        ]

        # ── 创建 Agents ──────────────────────────────
        self.agents = create_agents(tools)

        # ── 初始化 RAG 索引 ────────────────────────────
        self._init_rag_index()

    # ── RAG 索引 ──────────────────────────────────────

    def _init_rag_index(self) -> None:
        try:
            runs = self.db.get_all_runs_for_index()
            if runs:
                self.retriever.index_runs(runs)
        except Exception:
            pass

    def _sync_rag(self, run: dict[str, Any]) -> None:
        try:
            self.retriever.add_run(run)
        except Exception:
            pass

    # ── 主创作流程 ────────────────────────────────────

    def create_content(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行 Planner → Writer → Critic → Editor 流水线。

        Args:
            context: 创作参数，包含 content_type, user_prompt, audience, tone,
                     length_hint, extra_requirements, mode, model, template_id,
                     template_hint 等字段
        """
        tasks = create_content_tasks(self.agents)

        # CrewAI 的 inputs= 会替换 Task description 中的 {变量}
        crew = Crew(
            agents=[
                self.agents["planner"],
                self.agents["writer"],
                self.agents["critic"],
                self.agents["editor"],
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff(inputs=context)

        # ── 保存运行记录 ────────────────────────────
        run_id = str(uuid4())
        record = {
            "id": run_id,
            "created_at": utc_now(),
            "content_type": context.get("content_type", ""),
            "user_prompt": context.get("user_prompt", ""),
            "audience": context.get("audience", ""),
            "tone": context.get("tone", ""),
            "length_hint": context.get("length_hint", ""),
            "extra_requirements": context.get("extra_requirements", ""),
            "mode": context.get("mode", "fast"),
            "model": context.get("model", ""),
            "final_content": result.raw,
            "status": "completed",
            "steps": self._collect_steps(tasks),
            "template_id": context.get("template_id", ""),
            "parent_run_id": context.get("parent_run_id", ""),
            "iteration_round": context.get("iteration_round", 0),
        }
        self.db.save_run(record)
        self._sync_rag(record)

        # ── 检查进化触发 ────────────────────────────
        evolution_note = ""
        if self._should_evolve():
            evolution_note = "系统检测到足够反馈数据，建议在设置中触发自进化分析。"

        return {
            "run_id": run_id,
            "status": "completed",
            "mode": context.get("mode", "fast"),
            "model": context.get("model", ""),
            "final_content": result.raw,
            "steps": self._collect_steps(tasks),
            "evolution_available": self._should_evolve(),
            "evolution_note": evolution_note,
            "token_usage": str(result.token_usage) if hasattr(result, "token_usage") else "",
        }

    # ── 迭代修改 ──────────────────────────────────────

    def iterate_content(
        self, run_id: str, modification_request: str, mode: str = "", model: str = ""
    ) -> dict[str, Any]:
        """基于已有 run 的内容，根据用户修改意见进行迭代重生成。"""
        run = self.db.get_run(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        iteration_round = run.get("iteration_round", 0) + 1

        context = {
            "content_type": run.get("content_type", ""),
            "user_prompt": run.get("user_prompt", ""),
            "audience": run.get("audience", ""),
            "tone": run.get("tone", ""),
            "length_hint": run.get("length_hint", ""),
            "extra_requirements": (
                f"{run.get('extra_requirements', '')}\n"
                f"【用户修改意见（第{iteration_round}轮）】{modification_request}"
            ),
            "mode": mode or run.get("mode", "fast"),
            "model": model or run.get("model", ""),
            "template_id": run.get("template_id", ""),
            "template_hint": "",
            "parent_run_id": run_id,
            "iteration_round": iteration_round,
        }

        return self.create_content(context)

    # ── 进化触发 ──────────────────────────────────────

    def trigger_evolution(self) -> dict[str, Any]:
        """触发进化分析：Evolution Agent 分析反馈数据，生成优化建议。"""
        feedback_list = self.db.list_feedback()
        if len(feedback_list) < 3:
            return {
                "status": "skipped",
                "reason": "反馈数据不足（至少需要3条）",
                "suggestions": [],
            }

        runs = self.db.list_runs()
        successful = self.db.get_successful_runs(min_rating=4, limit=10)

        ratings = [f.get("rating") for f in feedback_list if isinstance(f.get("rating"), int)]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        feedback_summary = (
            f"总反馈数：{len(feedback_list)}\n"
            f"平均评分：{avg_rating:.1f}/5\n"
            f"高分案例数（≥4分）：{len(successful)}\n"
            f"最近反馈：\n"
            + "\n".join(
                f"  [{f.get('created_at', '')[:10]}] 评分{f.get('rating', '?')}/5 — {f.get('comment', '')[:120]}"
                for f in feedback_list[-10:]
            )
        )

        evolution_inputs = {
            "total_runs": str(len(runs)),
            "feedback_count": str(len(feedback_list)),
            "avg_rating": f"{avg_rating:.1f}",
            "successful_count": str(len(successful)),
            "user_preferences": self.db.get_memory_context(),
            "feedback_summary": feedback_summary,
        }

        evolution_task = create_evolution_task(self.agents, evolution_inputs)

        crew = Crew(
            agents=[self.agents["evolution"]],
            tasks=[evolution_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # 记录进化日志
        self.db.log_evolution({
            "agent": "Evolution",
            "output": result.raw,
            "avg_rating": avg_rating,
            "feedback_count": len(feedback_list),
        })

        return {
            "status": "completed",
            "analysis": result.raw,
            "avg_rating": round(avg_rating, 1),
            "feedback_count": len(feedback_list),
            "successful_count": len(successful),
        }

    # ── Prompt 管理 ────────────────────────────────────

    def get_current_prompts(self) -> dict[str, str]:
        """返回当前各 Agent 的配置信息（用于进化面板展示）。"""
        try:
            from pathlib import Path
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "agents.yaml"
            with open(config_path, encoding="utf-8") as f:
                agents_yaml = yaml.safe_load(f)
            return {
                name: agents_yaml.get(name, {}).get("backstory", "")[:500]
                for name in ["planner", "writer", "critic", "editor"]
            }
        except Exception:
            return {}

    def apply_evolution(self, prompts: dict[str, str]) -> dict[str, Any]:
        """将进化后的 prompt 持久化到 agents.yaml 并重建 Agent。"""
        applied: list[str] = []
        try:
            from pathlib import Path
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "agents.yaml"
            with open(config_path, encoding="utf-8") as f:
                agents_yaml = yaml.safe_load(f)

            for agent_name, new_backstory in prompts.items():
                agent_key = agent_name.lower()
                if agent_key in agents_yaml and new_backstory.strip():
                    agents_yaml[agent_key]["backstory"] = new_backstory.strip()
                    applied.append(agent_name)

            if applied:
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(agents_yaml, f, allow_unicode=True, default_flow_style=False)

                # 重建 Agent 使新配置立即生效
                tools = self._all_tools()
                self.agents = create_agents(tools)

            self.db.log_evolution({
                "agent": "Evolution",
                "output": f"Applied evolved prompts to: {', '.join(applied)}",
                "applied_agents": applied,
            })
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

        return {"status": "applied", "agents": applied}

    def reset_prompts(self) -> dict[str, Any]:
        """重置 Agent 配置：重新生成 agents.yaml 为默认值，并重建 Agent。"""
        try:
            from pathlib import Path
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "agents.yaml"

            # 恢复默认 YAML
            default_yaml = _default_agents_yaml()
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(default_yaml)

            # 重建 Agent
            tools = self._all_tools()
            self.agents = create_agents(tools)
            self.db.reset_evolved_prompts()  # 兼容旧数据
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

        return {"status": "reset"}

    # ── 模型管理 ──────────────────────────────────────

    def list_models(self) -> dict[str, Any]:
        """获取可用模型列表（通过 LLM 查询）。"""
        from .agents import create_llm
        try:
            llm = create_llm()
            # CrewAI 的 LLM 不直接暴露 list_models，通过底层 client 尝试
            models = []
            if hasattr(llm, "client") and hasattr(llm.client, "models"):
                try:
                    models = llm.client.models.list()
                except Exception:
                    pass
            items = [{"id": str(m.id), "owned_by": getattr(m, "owned_by", "")} for m in models]
        except Exception:
            items = []

        fast_model = os.environ.get("DEEPSEEK_FAST_MODEL", "deepseek-v4-flash")
        expert_model = os.environ.get("DEEPSEEK_EXPERT_MODEL", "deepseek-v4-pro")

        model_ids = {item["id"] for item in items}
        return {
            "items": items,
            "recommended": {"fast": fast_model, "expert": expert_model},
            "availability": {
                "fast": fast_model in model_ids,
                "expert": expert_model in model_ids,
            },
        }

    # ── 内部工具 ──────────────────────────────────────

    def _all_tools(self) -> list[Any]:
        """返回所有 Tool 实例的统一列表。"""
        return [
            self.rag_tool, self.kb_tool, self.memory_tool,
            self.web_search_tool, self.web_read_tool,
            self.youtube_tool, self.github_tool,
        ]

    @staticmethod
    def _collect_steps(tasks: list[Any]) -> list[dict[str, str]]:
        """从 Task 中提取各步骤的描述作为 steps 记录。"""
        steps: list[dict[str, str]] = []
        for task in tasks:
            agent_name = task.agent.role if task.agent else "Unknown"
            desc = task.description[:100] if task.description else ""
            output = ""
            if hasattr(task, "output") and task.output:
                output = str(task.output)[:200]
            steps.append({
                "agent": agent_name,
                "description": desc,
                "output_preview": output,
            })
        return steps

    def _should_evolve(self) -> bool:
        """判断是否应触发进化分析（≥5条反馈 且 距上次进化≥1小时）。"""
        feedback_count = self.db.count_feedback()
        if feedback_count < 5:
            return False
        latest = self.db.get_latest_evolution()
        if latest:
            try:
                from datetime import datetime, timezone
                last_time = datetime.fromisoformat(latest.get("timestamp", ""))
                elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
                if elapsed < 3600:
                    return False
            except (ValueError, TypeError):
                pass
        return True


def _default_agents_yaml() -> str:
    """返回默认的 agents.yaml 内容（用于 reset）。"""
    return """# 内容创作 Agent 角色定义
# 可直接修改此文件调整 Agent 行为，无需改 Python 代码

planner:
  role: "内容创作规划师"
  goal: "将用户需求拆解为结构化的可执行创作计划，参考历史成功案例和用户偏好制定最优策略"
  backstory: >
    你是一位资深内容策略师，擅长根据受众画像、语气要求和内容类型
    制定精准的创作大纲。你会主动检索历史成功案例，了解用户偏好，
    确保每个计划都有据可依、可执行、可验证。

writer:
  role: "内容创作者"
  goal: "严格按照创作大纲，写出高质量、语言自然、结构完整的内容初稿"
  backstory: >
    你是一位经验丰富的内容写手，精通多种文体（短视频脚本、公众号文章、
    产品文案、角色设定、小说开头等）。你严格遵循大纲约束，
    在规定篇幅内完成完整初稿，语言自然不做作，绝不写成提示词回答风格。

critic:
  role: "内容审稿人"
  goal: "像严格编辑一样审查初稿，从需求符合度、结构完整度、文风统一性、事实风险四个维度给出精准评审"
  backstory: >
    你是一位资深编辑审稿人，绝不泛泛表扬。你的评审标准明确、问题定位精准、
    修改建议可执行。每次评审必须给出四个维度的具体评分和改进方案。

editor:
  role: "终稿编辑"
  goal: "根据审稿意见对初稿进行精准改写，保留有效表达，交付可直接使用的最终版本"
  backstory: >
    你是一位资深内容编辑，擅长在不丢失原文优点的前提下进行针对性改写。
    你对文字有敏锐的判断力，知道哪些需要改、哪些保留，最终输出一定
    是"拿起来就能用"的成品。

evolution:
  role: "系统进化分析师"
  goal: "分析用户反馈数据，识别创作模式，提出针对各Agent的系统进化策略"
  backstory: >
    你是一位系统优化专家，擅长从用户反馈数据中发现深层模式和趋势。
    你的分析必须有数据支撑，建议必须可执行可验证，优先级从高到低排序。
    你关注的不只是提示词优化，还包括工作流调整、评分规则改进、模板优化。
"""
