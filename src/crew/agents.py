"""从 YAML 配置加载并创建 CrewAI Agent 实例。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, LLM

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_llm(model_name: str = "", temperature: float = 0.7) -> LLM:
    """创建 DeepSeek LLM 实例。

    CrewAI 1.15 原生支持 deepseek provider，格式为 'deepseek/<model_name>'。
    自定义 base_url 通过 extra_headers/environment 而非 base_url 参数。
    """
    api_key = (
        os.environ.get("PLANNER_API_KEY", "")
        or os.environ.get("WRITER_API_KEY", "")
        or os.environ.get("DEEPSEEK_API_KEY", "")
    )
    model = model_name or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

    # 如有自定义 base_url，设置环境变量让 deepseek provider 识别
    custom_base = os.environ.get("DEEPSEEK_BASE_URL", "").strip().rstrip("/")
    if custom_base and custom_base != "https://api.deepseek.com":
        os.environ.setdefault("DEEPSEEK_API_BASE", custom_base)

    return LLM(
        model=f"deepseek/{model}",
        api_key=api_key,
        temperature=temperature,
    )


def create_agents(tools: list[Any]) -> dict[str, Agent]:
    """从 config/agents.yaml 创建所有 Agent。

    Args:
        tools: CrewAI Tool 实例列表，会传给需要检索能力的 Agent

    Returns:
        {"planner": Agent, "writer": Agent, ...}
    """
    agent_configs = _load_yaml("agents")

    # 不同 Agent 使用不同的 LLM 和 temperature
    fast_model = os.environ.get("DEEPSEEK_FAST_MODEL", "")
    expert_model = os.environ.get("DEEPSEEK_EXPERT_MODEL", "")

    planner_llm = create_llm(fast_model, temperature=0.4)
    writer_llm = create_llm(fast_model, temperature=0.85)
    critic_llm = create_llm(expert_model, temperature=0.3)
    editor_llm = create_llm(expert_model, temperature=0.55)
    evolution_llm = create_llm(expert_model, temperature=0.4)

    def _make_agent(name: str, llm: LLM, agent_tools: list[Any] | None = None) -> Agent:
        cfg = agent_configs[name]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=agent_tools or [],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )

    return {
        "planner": _make_agent("planner", planner_llm, tools),  # Planner 有 Tool 使用权
        "writer": _make_agent("writer", writer_llm),
        "critic": _make_agent("critic", critic_llm),
        "editor": _make_agent("editor", editor_llm),
        "evolution": _make_agent("evolution", evolution_llm),
    }
