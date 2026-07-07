"""HTTP 服务器 —— 使用 CrewAI 驱动的 ContentCrew 替代原有 ContentOrchestrator。"""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .config import STATIC_DIR, STORE_DIR, get_config
from .db import Database
from .rag import Retriever
from .crew.crew import ContentCrew


CONFIG = get_config()
DB = Database(STORE_DIR)
RETRIEVER = Retriever()
CONTENT_CREW = ContentCrew(DB, RETRIEVER)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "ContentAgentMVP/0.3"  # CrewAI 迁移版本

    # ── routing ──────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # History
        if path == "/api/history":
            self._send_json({"items": DB.list_runs()})
            return

        # Single run
        if path == "/api/run":
            run_id = parse_qs(parsed.query).get("id", [""])[0]
            item = DB.get_run(run_id)
            if item is None:
                self._send_json({"error": "Run not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(item)
            return

        # Run iterations
        if path == "/api/run/iterations":
            run_id = parse_qs(parsed.query).get("id", [""])[0]
            runs = DB.list_runs()
            children = [
                r for r in runs
                if r.get("parent_run_id") == run_id or r.get("id") == run_id
            ]
            self._send_json({"items": children, "parent_id": run_id})
            return

        # Models
        if path == "/api/models":
            self._handle_models()
            return

        # Templates
        if path == "/api/templates":
            self._send_json({"items": DB.list_templates()})
            return

        # Single template
        if path.startswith("/api/templates/"):
            template_id = path.split("/api/templates/", 1)[1]
            tpl = DB.get_template(template_id)
            if tpl is None:
                self._send_json({"error": "Template not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(tpl)
            return

        # Memory profile
        if path == "/api/memory":
            self._send_json(DB.get_memory())
            return

        # Knowledge base
        if path == "/api/knowledge":
            keyword = parse_qs(parsed.query).get("q", [""])[0]
            if keyword:
                self._send_json({"items": DB.search_knowledge(keyword)})
            else:
                self._send_json({"items": DB.list_knowledge()})
            return

        # Evolution log
        if path == "/api/evolution":
            self._send_json({"items": DB.get_evolution_log()})
            return

        # Current prompts
        if path == "/api/prompts":
            self._send_json(CONTENT_CREW.get_current_prompts())
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/create":
            self._handle_create()
            return
        if path == "/api/iterate":
            self._handle_iterate()
            return
        if path == "/api/feedback":
            self._handle_feedback()
            return
        if path == "/api/evolution/trigger":
            self._handle_evolution_trigger()
            return
        if path == "/api/evolution/apply":
            self._handle_evolution_apply()
            return
        if path == "/api/prompts/reset":
            self._handle_prompts_reset()
            return
        if path == "/api/templates":
            self._handle_template_create()
            return
        if path == "/api/knowledge":
            self._handle_knowledge_create()
            return
        if path == "/api/run/delete":
            self._handle_delete_run_post()
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/templates/"):
            template_id = path.split("/api/templates/", 1)[1]
            self._handle_template_update(template_id)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/run":
            self._handle_delete_run(parsed.query)
            return
        if path.startswith("/api/templates/"):
            template_id = path.split("/api/templates/", 1)[1]
            self._handle_template_delete(template_id)
            return
        if path.startswith("/api/knowledge/"):
            entry_id = path.split("/api/knowledge/", 1)[1]
            self._handle_knowledge_delete(entry_id)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    # ── logging ──────────────────────────────────────────

    def log_message(self, format: str, *args: object) -> None:
        from datetime import datetime
        msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.client_address[0]} {format % args}"
        print(msg)
        try:
            log_path = STORE_DIR / "server.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            lines = log_path.read_text(encoding="utf-8").splitlines()
            if len(lines) > 1000:
                log_path.write_text("\n".join(lines[-1000:]) + "\n", encoding="utf-8")
        except Exception:
            pass

    # ── create ────────────────────────────────────────────

    def _handle_create(self) -> None:
        try:
            payload = self._read_json_body()
            self._validate_payload(payload)

            # 构建 context dict（替代原来的 CreationRequest）
            context = {
                "content_type": str(payload.get("content_type", "")).strip(),
                "user_prompt": str(payload.get("user_prompt", "")).strip(),
                "audience": str(payload.get("audience", "")).strip() or "未指定",
                "tone": str(payload.get("tone", "")).strip() or "专业自然",
                "length_hint": str(payload.get("length_hint", "")).strip() or "中等",
                "extra_requirements": str(payload.get("extra_requirements", "")).strip() or "无",
                "mode": payload.get("mode", "fast"),
                "model": payload.get("model", ""),
                "template_id": payload.get("template_id", ""),
                "template_hint": self._resolve_template_hint(payload.get("template_id", "")),
                "parent_run_id": str(payload.get("parent_run_id", "")),
                "iteration_round": int(payload.get("iteration_round", 0) or 0),
            }

            result = CONTENT_CREW.create_content(context)
            self._send_json(result)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── iterate ───────────────────────────────────────────

    def _handle_iterate(self) -> None:
        try:
            payload = self._read_json_body()
            run_id = str(payload.get("run_id", "")).strip()
            modification = str(payload.get("modification_request", "")).strip()
            if not run_id:
                raise ValueError("run_id is required")
            if not modification:
                raise ValueError("modification_request is required")

            mode = payload.get("mode", "")
            model = payload.get("model", "")
            result = CONTENT_CREW.iterate_content(run_id, modification, mode=mode, model=model)
            self._send_json(result)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── feedback ──────────────────────────────────────────

    def _handle_feedback(self) -> None:
        try:
            payload = self._read_json_body()
            run_id = str(payload.get("run_id", "")).strip()
            if not run_id:
                raise ValueError("run_id is required")
            rating_raw = payload.get("rating")
            rating = int(rating_raw) if rating_raw not in (None, "") else None
            comment = str(payload.get("comment", "")).strip()
            DB.save_feedback(run_id, rating, comment)
            self._send_json({
                "status": "ok",
                "evolution_recommended": CONTENT_CREW._should_evolve(),
            })
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── evolution ─────────────────────────────────────────

    def _handle_evolution_trigger(self) -> None:
        try:
            result = CONTENT_CREW.trigger_evolution()
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_evolution_apply(self) -> None:
        try:
            payload = self._read_json_body()
            prompts = payload.get("prompts", {})
            if not prompts:
                raise ValueError("prompts is required")
            result = CONTENT_CREW.apply_evolution(prompts)
            self._send_json(result)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_prompts_reset(self) -> None:
        try:
            result = CONTENT_CREW.reset_prompts()
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── templates ─────────────────────────────────────────

    def _handle_template_create(self) -> None:
        try:
            payload = self._read_json_body()
            tpl_id = payload.get("id", f"tpl_{hash(json.dumps(DB.list_templates()))}")
            template = {
                "id": tpl_id,
                "name": payload.get("name", ""),
                "content_type": payload.get("content_type", ""),
                "description": payload.get("description", ""),
                "default_tone": payload.get("default_tone", ""),
                "default_audience": payload.get("default_audience", ""),
                "default_length": payload.get("default_length", "中等"),
                "system_hint": payload.get("system_hint", ""),
            }
            DB.save_template(template)
            self._send_json({"status": "ok", "template": template})
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_template_update(self, template_id: str) -> None:
        try:
            payload = self._read_json_body()
            updates = {k: v for k, v in payload.items() if k != "id"}
            ok = DB.update_template(template_id, updates)
            if not ok:
                self._send_json({"error": "Template not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json({"status": "ok"})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_template_delete(self, template_id: str) -> None:
        ok = DB.delete_template(template_id)
        if not ok:
            self._send_json({"error": "Template not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json({"status": "ok", "id": template_id})

    # ── knowledge base ────────────────────────────────────

    def _handle_knowledge_create(self) -> None:
        try:
            payload = self._read_json_body()
            entry = {
                "title": payload.get("title", ""),
                "content": payload.get("content", ""),
                "tags": payload.get("tags", []),
                "content_type": payload.get("content_type", ""),
            }
            if not entry["title"].strip() or not entry["content"].strip():
                raise ValueError("title and content are required")
            DB.add_knowledge(entry)
            self._send_json({"status": "ok"})
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_knowledge_delete(self, entry_id: str) -> None:
        ok = DB.delete_knowledge(entry_id)
        if not ok:
            self._send_json({"error": "Knowledge entry not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json({"status": "ok", "id": entry_id})

    # ── models ────────────────────────────────────────────

    def _handle_models(self) -> None:
        try:
            self._send_json(CONTENT_CREW.list_models())
        except Exception as exc:
            self._send_json({
                "items": [],
                "recommended": {
                    "fast": CONFIG.deepseek_fast_model,
                    "expert": CONFIG.deepseek_expert_model,
                },
                "availability": {"fast": False, "expert": False},
                "error": str(exc),
            })

    # ── delete run ────────────────────────────────────────

    def _handle_delete_run_post(self) -> None:
        try:
            payload = self._read_json_body()
            run_id = str(payload.get("id", "")).strip()
            if not run_id:
                raise ValueError("id is required")
            deleted = DB.delete_run(run_id)
            if not deleted:
                self._send_json({"error": "Run not found"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                RETRIEVER.remove_run(run_id)
            except Exception:
                pass
            self._send_json({"status": "ok", "id": run_id})
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_delete_run(self, query: str) -> None:
        run_id = parse_qs(query).get("id", [""])[0].strip()
        if not run_id:
            self._send_json({"error": "id is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        deleted = DB.delete_run(run_id)
        if not deleted:
            self._send_json({"error": "Run not found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            RETRIEVER.remove_run(run_id)
        except Exception:
            pass
        self._send_json({"status": "ok", "id": run_id})

    # ── static files ──────────────────────────────────────

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("/", "") else path.lstrip("/")
        file_path = (STATIC_DIR / relative).resolve()

        if not str(file_path).startswith(str(STATIC_DIR.resolve())) or not file_path.exists():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        mime, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        content_type = mime or "application/octet-stream"
        if content_type.startswith("text/"):
            content_type = f"{content_type}; charset=utf-8"
        if content_type == "application/javascript":
            content_type = "application/javascript; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── helpers ───────────────────────────────────────────

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    @staticmethod
    def _validate_payload(payload: dict) -> None:
        if not str(payload.get("user_prompt", "")).strip():
            raise ValueError("user_prompt is required")
        if not str(payload.get("content_type", "")).strip():
            raise ValueError("content_type is required")

    def _resolve_template_hint(self, template_id: str) -> str:
        if not template_id:
            return ""
        tpl = DB.get_template(template_id)
        return tpl.get("system_hint", "") if tpl else ""

    def _send_json(self, payload: dict | list, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server() -> None:
    host, port = CONFIG.host, CONFIG.port
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"EcRoom server started at http://{host}:{port}")
    print("  Powered by CrewAI — Planner → Writer → Critic → Editor")
    server.serve_forever()
