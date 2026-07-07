from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.runs_path = data_dir / "runs.json"
        self.feedback_path = data_dir / "feedback.json"
        self.preferences_path = data_dir / "preferences.json"
        self.memory_path = data_dir / "memory.json"
        self.evolution_path = data_dir / "evolution.json"
        self.templates_path = data_dir / "templates.json"
        self.knowledge_path = data_dir / "knowledge_base.json"
        self.evolved_prompts_path = data_dir / "evolved_prompts.json"
        self._init_schema()

    # ── schema ────────────────────────────────────────────

    def _init_schema(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        self._ensure_json_file(self.runs_path, [])
        self._ensure_json_file(self.feedback_path, [])
        self._ensure_json_file(self.preferences_path, {})
        self._ensure_json_file(self.memory_path, self._default_memory())
        self._ensure_json_file(self.evolution_path, [])
        self._ensure_json_file(self.templates_path, self._default_templates())
        self._ensure_json_file(self.knowledge_path, [])
        self._ensure_json_file(self.evolved_prompts_path, {})

    @staticmethod
    def _ensure_json_file(path: Path, default: list | dict) -> None:
        if not path.exists():
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── runs ──────────────────────────────────────────────

    def save_run(self, payload: dict[str, Any]) -> None:
        runs = self._read_json(self.runs_path)
        runs.append(payload)
        self._write_json(self.runs_path, runs)

    def update_run(self, run_id: str, updates: dict[str, Any]) -> bool:
        runs = self._read_json(self.runs_path)
        for row in runs:
            if row["id"] == run_id:
                row.update(updates)
                self._write_json(self.runs_path, runs)
                return True
        return False

    def list_runs(self) -> list[dict[str, Any]]:
        runs = self._read_json(self.runs_path)
        items = [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "content_type": row["content_type"],
                "user_prompt": row["user_prompt"],
                "final_content": row.get("final_content") or "",
                "status": row["status"],
                "mode": row.get("mode", "fast"),
                "model": row.get("model", ""),
            }
            for row in runs
        ]
        return sorted(items, key=lambda item: item["created_at"], reverse=True)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        runs = self._read_json(self.runs_path)
        for row in runs:
            if row["id"] == run_id:
                return row
        return None

    def delete_run(self, run_id: str) -> bool:
        runs = self._read_json(self.runs_path)
        next_runs = [row for row in runs if row["id"] != run_id]
        if len(next_runs) == len(runs):
            return False

        feedback = self._read_json(self.feedback_path)
        next_feedback = [row for row in feedback if row.get("run_id") != run_id]

        self._write_json(self.runs_path, next_runs)
        self._write_json(self.feedback_path, next_feedback)
        return True

    def get_successful_runs(self, min_rating: int = 4, limit: int = 20) -> list[dict[str, Any]]:
        """Return runs that have high-rated feedback, for memory/evolution analysis."""
        runs = self._read_json(self.runs_path)
        feedback = self._read_json(self.feedback_path)
        high_rated_ids = {
            row["run_id"]
            for row in feedback
            if isinstance(row.get("rating"), int) and row["rating"] >= min_rating
        }
        successful = [row for row in runs if row["id"] in high_rated_ids]
        return sorted(successful, key=lambda r: r.get("created_at", ""), reverse=True)[:limit]

    # ── feedback ───────────────────────────────────────────

    def save_feedback(self, run_id: str, rating: int | None, comment: str) -> None:
        created_at = utc_now()
        feedback = self._read_json(self.feedback_path)
        feedback.append(
            {
                "run_id": run_id,
                "rating": rating,
                "comment": comment,
                "created_at": created_at,
            }
        )
        self._write_json(self.feedback_path, feedback)
        self._update_preferences_from_feedback(run_id, rating, comment)
        self._update_memory_from_feedback(run_id, rating, comment)

    def list_feedback(self) -> list[dict[str, Any]]:
        return self._read_json(self.feedback_path)

    def get_feedback_for_run(self, run_id: str) -> dict[str, Any] | None:
        feedback = self._read_json(self.feedback_path)
        for row in feedback:
            if row.get("run_id") == run_id:
                return row
        return None

    def count_feedback(self) -> int:
        return len(self._read_json(self.feedback_path))

    # ── preferences (legacy, kept for backward compat) ────

    def _update_preferences_from_feedback(self, run_id: str, rating: int | None, comment: str) -> None:
        run = self.get_run(run_id)
        if run is None:
            return

        updates: dict[str, str] = {}
        if rating is not None and rating >= 4 and run.get("tone"):
            updates["preferred_tone"] = run["tone"]
        if rating is not None and rating >= 4 and run.get("content_type"):
            updates["preferred_content_type"] = run["content_type"]
        if comment.strip():
            updates["latest_feedback_note"] = comment.strip()

        if not updates:
            return

        timestamp = utc_now()
        preferences = self._read_json(self.preferences_path)
        for key, value in updates.items():
            preferences[key] = {"value": value, "updated_at": timestamp}
        self._write_json(self.preferences_path, preferences)

    def get_preferences(self) -> dict[str, str]:
        rows = self._read_json(self.preferences_path)
        return {key: value["value"] for key, value in rows.items()}

    # ── memory (rich user profile) ────────────────────────

    @staticmethod
    def _default_memory() -> dict[str, Any]:
        return {
            "user_profile": {
                "preferred_tones": {},       # {tone: weight}
                "preferred_content_types": {},  # {type: weight}
                "preferred_structures": {},     # {structure_desc: weight}
                "common_audiences": [],          # [audience, ...]
                "length_preference": "中等",
                "writing_patters": {},
            },
            "successful_patterns": [],       # [{pattern, source_run_id, rating}]
            "last_updated": "",
        }

    def _update_memory_from_feedback(self, run_id: str, rating: int | None, comment: str) -> None:
        if rating is None or rating < 4:
            return

        run = self.get_run(run_id)
        if run is None:
            return

        memory = self._read_json(self.memory_path)
        profile = memory.get("user_profile", {})

        # Update tone preferences
        tone = run.get("tone", "").strip()
        if tone:
            tones = profile.setdefault("preferred_tones", {})
            tones[tone] = round(tones.get(tone, 0) + rating * 0.1, 2)

        # Update content type preferences
        ct = run.get("content_type", "").strip()
        if ct:
            cts = profile.setdefault("preferred_content_types", {})
            cts[ct] = round(cts.get(ct, 0) + rating * 0.1, 2)

        # Update audience history
        audience = run.get("audience", "").strip()
        if audience and audience not in profile.get("common_audiences", []):
            audiences = profile.setdefault("common_audiences", [])
            audiences.append(audience)
            if len(audiences) > 10:
                audiences.pop(0)

        # Record successful pattern
        final_content = run.get("final_content", "")
        if final_content and len(final_content) > 100:
            patterns = memory.get("successful_patterns", [])
            patterns.append({
                "run_id": run_id,
                "content_type": ct,
                "tone": tone,
                "rating": rating,
                "preview": final_content[:200],
                "created_at": utc_now(),
            })
            # Keep last 30
            memory["successful_patterns"] = patterns[-30:]

        memory["user_profile"] = profile
        memory["last_updated"] = utc_now()
        self._write_json(self.memory_path, memory)

    def get_memory(self) -> dict[str, Any]:
        return self._read_json(self.memory_path)

    def get_memory_context(self, content_type: str = "", audience: str = "") -> str:
        """Build a concise memory context string for agent injection."""
        memory = self._read_json(self.memory_path)
        profile = memory.get("user_profile", {})
        patterns = memory.get("successful_patterns", [])

        parts: list[str] = []

        # Tone preferences
        tones = profile.get("preferred_tones", {})
        if tones:
            sorted_tones = sorted(tones.items(), key=lambda x: x[1], reverse=True)[:3]
            parts.append(f"偏好语气：{', '.join(f'{t}({w:.1f})' for t, w in sorted_tones)}")

        # Content type preferences
        cts = profile.get("preferred_content_types", {})
        if cts:
            sorted_cts = sorted(cts.items(), key=lambda x: x[1], reverse=True)[:3]
            parts.append(f"擅长内容类型：{', '.join(f'{c}({w:.1f})' for c, w in sorted_cts)}")

        # Recent successful patterns
        relevant_patterns = patterns
        if content_type:
            relevant_patterns = [p for p in patterns if p.get("content_type") == content_type] or patterns
        if relevant_patterns:
            recent = relevant_patterns[-3:]
            previews = "\n".join(
                f"  [{p.get('content_type', '')}] {p.get('preview', '')[:120]}..."
                for p in recent
            )
            parts.append(f"近期高分案例预览：\n{previews}")

        # Length preference
        lp = profile.get("length_preference", "")
        if lp:
            parts.append(f"长度偏好：{lp}")

        return "\n".join(parts) if parts else "暂无历史记忆"

    # ── evolution log ──────────────────────────────────────

    def log_evolution(self, entry: dict[str, Any]) -> None:
        log = self._read_json(self.evolution_path)
        log.append({**entry, "timestamp": utc_now()})
        self._write_json(self.evolution_path, log)

    def get_evolution_log(self) -> list[dict[str, Any]]:
        return self._read_json(self.evolution_path)

    def get_latest_evolution(self, agent_name: str = "") -> dict[str, Any] | None:
        log = self._read_json(self.evolution_path)
        if agent_name:
            for entry in reversed(log):
                if entry.get("agent") == agent_name:
                    return entry
        return log[-1] if log else None

    # ── templates ──────────────────────────────────────────

    @staticmethod
    def _default_templates() -> list[dict[str, Any]]:
        return [
            {
                "id": "tpl_short_video",
                "name": "短视频脚本",
                "content_type": "短视频脚本",
                "description": "适合抖音/B站的口播脚本，强调节奏感和钩子",
                "default_tone": "自然有劲",
                "default_audience": "泛知识用户",
                "default_length": "中等",
                "system_hint": "开头3秒必须有钩子，中间有反转或信息增量，结尾有行动号召。",
            },
            {
                "id": "tpl_wechat_article",
                "name": "公众号文章",
                "content_type": "公众号文章",
                "description": "深度长文风格，适合微信生态阅读",
                "default_tone": "专业亲切",
                "default_audience": "专业读者",
                "default_length": "详细",
                "system_hint": "标题要有吸引力但不标题党，正文有逻辑层次，排版友好。",
            },
            {
                "id": "tpl_product_copy",
                "name": "产品文案",
                "content_type": "产品文案",
                "description": "品牌传播向的产品文案，强调卖点和调性",
                "default_tone": "锐利克制",
                "default_audience": "品牌主理人",
                "default_length": "简短",
                "system_hint": "一句话讲清核心卖点，避免堆砌形容词，保持品牌一致性。",
            },
            {
                "id": "tpl_character_setting",
                "name": "角色设定",
                "content_type": "角色设定",
                "description": "世界观角色的设定文案，要求有辨识度",
                "default_tone": "冷感克制",
                "default_audience": "二次元与剧情向用户",
                "default_length": "中等",
                "system_hint": "先建角色内核（欲望+缺口+行为），再写登场场景。",
            },
            {
                "id": "tpl_novel_opening",
                "name": "小说开头",
                "content_type": "小说开头",
                "description": "小说前三章/开头场景，快速建立世界观和人物弧光",
                "default_tone": "细腻有张力",
                "default_audience": "小说读者",
                "default_length": "详细",
                "system_hint": "第一句就要有悬念，快速建立世界观和主要冲突。",
            },
        ]

    def list_templates(self) -> list[dict[str, Any]]:
        return self._read_json(self.templates_path)

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        templates = self._read_json(self.templates_path)
        for tpl in templates:
            if tpl["id"] == template_id:
                return tpl
        return None

    def save_template(self, template: dict[str, Any]) -> None:
        templates = self._read_json(self.templates_path)
        templates.append(template)
        self._write_json(self.templates_path, templates)

    def update_template(self, template_id: str, updates: dict[str, Any]) -> bool:
        templates = self._read_json(self.templates_path)
        for tpl in templates:
            if tpl["id"] == template_id:
                tpl.update(updates)
                self._write_json(self.templates_path, templates)
                return True
        return False

    def delete_template(self, template_id: str) -> bool:
        templates = self._read_json(self.templates_path)
        next_templates = [t for t in templates if t["id"] != template_id]
        if len(next_templates) == len(templates):
            return False
        self._write_json(self.templates_path, next_templates)
        return True

    # ── knowledge base ─────────────────────────────────────

    def list_knowledge(self) -> list[dict[str, Any]]:
        return self._read_json(self.knowledge_path)

    def add_knowledge(self, entry: dict[str, Any]) -> None:
        kb = self._read_json(self.knowledge_path)
        kb.append({**entry, "id": entry.get("id", f"kb_{utc_now().replace(':', '-')}"), "created_at": utc_now()})
        self._write_json(self.knowledge_path, kb)

    def delete_knowledge(self, entry_id: str) -> bool:
        kb = self._read_json(self.knowledge_path)
        next_kb = [e for e in kb if e.get("id") != entry_id]
        if len(next_kb) == len(kb):
            return False
        self._write_json(self.knowledge_path, next_kb)
        return True

    def search_knowledge(self, keyword: str) -> list[dict[str, Any]]:
        kb = self._read_json(self.knowledge_path)
        keyword_lower = keyword.lower()
        results = [
            e for e in kb
            if keyword_lower in str(e.get("title", "")).lower()
            or keyword_lower in str(e.get("content", "")).lower()
            or keyword_lower in str(e.get("tags", "")).lower()
        ]
        return results

    # ── full context for RAG ───────────────────────────────

    def get_all_runs_for_index(self) -> list[dict[str, Any]]:
        """Return all completed runs with content for RAG indexing."""
        runs = self._read_json(self.runs_path)
        return [r for r in runs if r.get("final_content") and r.get("status") == "completed"]

    # ── evolved prompts ────────────────────────────────────

    def get_evolved_prompts(self) -> dict[str, str]:
        """Return {agent_name: evolved_system_prompt} or {}."""
        return self._read_json(self.evolved_prompts_path)

    def save_evolved_prompts(self, prompts: dict[str, str]) -> None:
        """Save evolved prompts, merging with existing."""
        current = self._read_json(self.evolved_prompts_path)
        current.update(prompts)
        current["last_updated"] = utc_now()
        self._write_json(self.evolved_prompts_path, current)

    def reset_evolved_prompts(self) -> None:
        """Reset all evolved prompts to factory defaults."""
        self._write_json(self.evolved_prompts_path, {})
