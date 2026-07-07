"""GitHub 搜索 Tool —— 通过 gh CLI 搜索仓库、代码、Issue。"""

from __future__ import annotations

import subprocess
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GitHubSearchInput(BaseModel):
    """GitHub 搜索参数"""
    query: str = Field(description="搜索查询，如 'LLM framework stars:>100'、'image classification CNN'")


class GitHubTool(BaseTool):
    """在 GitHub 上搜索开源仓库、代码和 Issue。需要系统已安装 gh CLI。"""

    name: str = "GitHub搜索"
    description: str = (
        "在 GitHub 上搜索开源仓库。返回仓库名称、描述、star 数、URL。"
        "适合查找技术实现参考、开源工具、代码示例等。"
    )
    args_schema: Type[BaseModel] = GitHubSearchInput

    def _run(self, query: str) -> str:
        if not self._has_gh():
            return (
                "gh CLI 未安装，无法搜索 GitHub。安装方法：\n"
                "  winget install GitHub.cli\n"
                "或访问 https://cli.github.com/"
            )

        try:
            result = subprocess.run(
                ["gh", "search", "repos", query, "--sort", "stars", "--limit", "5"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                err = result.stderr.strip()
                # 未登录
                if "auth" in err.lower() or "login" in err.lower():
                    return "需要先登录 GitHub：运行 gh auth login"
                return f"GitHub 搜索失败：{err[:300]}"

            output = result.stdout.strip()
            if not output:
                return "未找到匹配的 GitHub 仓库。"
            return output
        except FileNotFoundError:
            return "gh CLI 未安装。安装：winget install GitHub.cli"
        except subprocess.TimeoutExpired:
            return "GitHub 搜索超时，请稍后重试。"
        except Exception as exc:
            return f"GitHub 搜索失败：{exc}"

    @staticmethod
    def _has_gh() -> bool:
        try:
            subprocess.run(
                ["gh", "--version"],
                capture_output=True, timeout=10,
            )
            return True
        except Exception:
            return False
