"""전역 설정·시크릿 매니저 — .env를 읽는 유일한 지점.

다른 코드에서 os.environ 직접 접근 금지 (작업지시서 §1 원칙 7).
모델 스위치는 모델구성_정책프롬프트_v1 §1을 따른다.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    database_url: str

    scenario: str = "a"

    npc_llm_provider: str = "fake"
    npc_llm_model: str = "exaone3.5:7.8b"
    npc_age7_policy: str = "on"
    core_llm_provider: str = "fake"
    core_llm_model: str = "gemma3:12b"
    embedding_provider: str = "fake"
    embedding_fallback: str = "qwen3-local"
    ollama_base_url: str = "http://localhost:11434"

    system_harness: str = "on"
    cookie_ab: str = "on"
    paw_reason_ab: str = "on"

    inspector_token: str = "pigfarm-dev-inspector"
    gemini_api_key: str = ""
    gemini_requests_per_minute: int = Field(default=10, gt=0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
