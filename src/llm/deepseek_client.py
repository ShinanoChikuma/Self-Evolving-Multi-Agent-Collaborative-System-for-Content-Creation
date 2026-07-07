from __future__ import annotations

import json
from typing import Any
from urllib import error, request


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1800,
        model: str | None = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"DeepSeek API HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"DeepSeek API connection failed: {exc.reason}") from exc

        parsed: dict[str, Any] = json.loads(body)
        choices = parsed.get("choices") or []
        if not choices:
            raise RuntimeError(f"DeepSeek API returned no choices: {body}")

        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"DeepSeek API returned empty content: {body}")
        return content.strip()

    def list_models(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/models"
        req = request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            method="GET",
        )

        try:
            with request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"DeepSeek model list HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"DeepSeek model list failed: {exc.reason}") from exc

        parsed: dict[str, Any] = json.loads(body)
        items = parsed.get("data")
        if not isinstance(items, list):
            raise RuntimeError(f"DeepSeek model list returned invalid payload: {body}")
        return items
