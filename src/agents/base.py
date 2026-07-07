from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ChatClient(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1800,
        model: str | None = None,
    ) -> str:
        ...


@dataclass
class AgentResult:
    agent: str
    output: str


class BaseAgent:
    name = "base"
    system_prompt = ""
    temperature = 0.7
    max_tokens = 1800

    def __init__(self, client: ChatClient) -> None:
        self.client = client

    def build_user_prompt(self, context: dict[str, str]) -> str:
        raise NotImplementedError

    def run(self, context: dict[str, str], *, model: str | None = None) -> AgentResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.build_user_prompt(context)},
        ]
        output = self.client.chat(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            model=model,
        )
        return AgentResult(agent=self.name, output=output)
