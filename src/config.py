from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
STATIC_DIR = ROOT_DIR / "static"
DATA_DIR = ROOT_DIR / "data"
STORE_DIR = DATA_DIR


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    deepseek_base_url: str
    deepseek_model: str
    deepseek_fast_model: str
    deepseek_expert_model: str
    planner_api_key: str
    writer_api_key: str
    editor_api_key: str
    critic_api_key: str
    memory_api_key: str
    evolution_api_key: str


def get_config() -> AppConfig:
    load_env_file(ENV_PATH)
    DATA_DIR.mkdir(exist_ok=True)

    def require(name: str) -> str:
        value = os.environ.get(name, "").strip()
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    default_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash"
    fast_model = os.environ.get("DEEPSEEK_FAST_MODEL", default_model).strip() or default_model
    expert_model = os.environ.get("DEEPSEEK_EXPERT_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro"

    return AppConfig(
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("APP_PORT", "8000")),
        deepseek_base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=default_model,
        deepseek_fast_model=fast_model,
        deepseek_expert_model=expert_model,
        planner_api_key=require("PLANNER_API_KEY"),
        writer_api_key=require("WRITER_API_KEY"),
        editor_api_key=require("EDITOR_API_KEY"),
        critic_api_key=require("CRITIC_API_KEY"),
        memory_api_key=os.environ.get("MEMORY_API_KEY", ""),
        evolution_api_key=os.environ.get("EVOLUTION_API_KEY", ""),
    )
