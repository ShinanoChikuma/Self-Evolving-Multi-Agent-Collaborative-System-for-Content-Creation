"""YouTube 字幕提取 Tool —— 通过 yt-dlp 获取视频字幕文本。"""

from __future__ import annotations

import subprocess
import tempfile
import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class YouTubeInput(BaseModel):
    """YouTube 参数"""
    url: str = Field(description="YouTube 视频 URL，如 'https://www.youtube.com/watch?v=...'")


class YouTubeTool(BaseTool):
    """提取 YouTube 视频字幕文本。需要系统已安装 yt-dlp。"""

    name: str = "YouTube字幕"
    description: str = (
        "提取 YouTube 视频的字幕文本（支持中英文自动字幕）。"
        "适合需要了解视频内容、总结教程、引用视频观点等场景。"
        "返回字幕全文。"
    )
    args_schema: Type[BaseModel] = YouTubeInput

    def _run(self, url: str) -> str:
        # 检测 yt-dlp
        if not self._has_ytdlp():
            return (
                "yt-dlp 未安装，无法提取字幕。请运行：pip install yt-dlp"
            )

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    "yt-dlp",
                    "--write-auto-subs",
                    "--sub-lang", "zh-Hans,zh,en",
                    "--skip-download",
                    "--convert-subs", "srt",
                    "--output", os.path.join(tmpdir, "%(id)s"),
                    url,
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                # 尝试读取生成的字幕文件
                srt_files = [
                    f for f in os.listdir(tmpdir)
                    if f.endswith(".srt") or f.endswith(".vtt")
                ]
                if srt_files:
                    srt_path = os.path.join(tmpdir, srt_files[0])
                    with open(srt_path, encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    # 移除时间戳，只保留纯文本
                    lines = []
                    for line in text.split("\n"):
                        line = line.strip()
                        if line and not line.isdigit() and "-->" not in line:
                            lines.append(line)
                    content = "\n".join(lines)
                    if len(content) > 4000:
                        content = content[:4000] + "\n\n...（字幕过长，已截断）"
                    return content or "字幕文件为空。"
                else:
                    return f"未找到字幕。视频可能没有自动生成的字幕。\nyt-dlp 输出：{result.stderr[-500:]}"
        except subprocess.TimeoutExpired:
            return "提取字幕超时，请稍后重试。"
        except FileNotFoundError:
            return "yt-dlp 未安装。请运行：pip install yt-dlp"
        except Exception as exc:
            return f"提取字幕失败：{exc}"

    @staticmethod
    def _has_ytdlp() -> bool:
        try:
            subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True, timeout=10,
            )
            return True
        except Exception:
            return False
