"""网页阅读 Tool —— 通过 Jina Reader 将任意网页转为干净的 Markdown 文本。"""

from __future__ import annotations

import urllib.request
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WebReadInput(BaseModel):
    """网页阅读参数"""
    url: str = Field(description="要读取的网页 URL，如 'https://example.com/article'")


class WebReadTool(BaseTool):
    """读取任意网页的完整内容（转为干净文本）。无需配置，开箱即用。"""

    name: str = "网页阅读"
    description: str = (
        "读取指定 URL 的网页内容，返回干净的 Markdown 格式文本。"
        "适合阅读文章、产品页面、技术文档等。需要完整的 http/https URL。"
    )
    args_schema: Type[BaseModel] = WebReadInput

    def _run(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            jina_url = f"https://r.jina.ai/{url}"
            req = urllib.request.Request(
                jina_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; ContentCrew/1.0)",
                    "Accept": "text/plain",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            if not content.strip():
                return "该网页内容为空或无法解析。"
            # 限制返回长度，避免超出 Agent context
            if len(content) > 3000:
                content = content[:3000] + "\n\n...（内容过长，已截断）"
            return content
        except urllib.error.HTTPError as exc:
            return f"无法读取该网页（HTTP {exc.code}）。请检查 URL 是否正确。"
        except urllib.error.URLError as exc:
            return f"无法连接：{exc.reason}"
        except Exception as exc:
            return f"读取网页失败：{exc}"
