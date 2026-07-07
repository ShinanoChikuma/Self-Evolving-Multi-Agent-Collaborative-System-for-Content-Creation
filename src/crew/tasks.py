"""从 YAML 配置加载并创建 CrewAI Task 实例。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from crewai import Task

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_content_tasks(agents: dict[str, Any]) -> list[Task]:
    """创建内容创作流水线的 4 个 Task：Plan → Write → Critique → Edit。

    Task 之间的 context 自动传递：write_task 的 description 中可用
    {plan_task} 获取 plan_task 的输出。
    """
    task_configs = _load_yaml("tasks")

    plan_task = Task(
        description=task_configs["plan_task"]["description"],
        expected_output=task_configs["plan_task"]["expected_output"],
        agent=agents["planner"],
    )

    write_task = Task(
        description=task_configs["write_task"]["description"],
        expected_output=task_configs["write_task"]["expected_output"],
        agent=agents["writer"],
        context=[plan_task],  # {plan_task} → plan_task.raw
    )

    critique_task = Task(
        description=task_configs["critique_task"]["description"],
        expected_output=task_configs["critique_task"]["expected_output"],
        agent=agents["critic"],
        context=[write_task],  # {write_task} → write_task.raw
    )

    edit_task = Task(
        description=task_configs["edit_task"]["description"],
        expected_output=task_configs["edit_task"]["expected_output"],
        agent=agents["editor"],
        context=[write_task, critique_task],  # {write_task} / {critique_task}
    )

    return [plan_task, write_task, critique_task, edit_task]


def create_evolution_task(
    agents: dict[str, Any],
    inputs: dict[str, Any],
) -> Task:
    """创建进化分析 Task。"""
    task_configs = _load_yaml("tasks")
    cfg = task_configs["evolution_task"]

    # 将 inputs 注入 description（占位符替换）
    description = cfg["description"].format(**inputs)

    return Task(
        description=description,
        expected_output=cfg["expected_output"],
        agent=agents["evolution"],
    )
