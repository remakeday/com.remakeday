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
    npc_llm_model: str = "kanana1.5:8b-q4km"
    npc_llm_think: str = "off"
    npc_age7_policy: str = "on"
    core_llm_provider: str = "fake"
    core_llm_model: str = "gemma4:12b"
    core_llm_think: str = "off"
    embedding_provider: str = "fake"
    embedding_fallback: str = "qwen3-local"
    ollama_base_url: str = "http://localhost:11434"

    system_harness: str = "on"
    cookie_ab: str = "on"
    paw_reason_ab: str = "on"

    inspector_token: str = ""  # 비어 있으면 인스펙터 라우트 비활성(404) — 값은 .env에만
    gemini_api_key: str = ""
    gemini_requests_per_minute: int = Field(default=10, gt=0)
    anthropic_api_key: str = ""
    anthropic_effort: str = "low"
    anthropic_max_tokens: int = 8192
    anthropic_timeout: float = 120.0

    # Google OAuth 로그인 — .env의 GOOGLE_OAUTH_* / SESSION_SECRET / FRONTEND_BASE_URL
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8500/api/v1/auth/google/callback"
    session_secret: str = "dev-session-secret-change-me"
    frontend_base_url: str = "http://localhost:3500"

    # 과잉 사용 방지 허들
    guard_auth: str = "on"
    trust_proxy: bool = False
    user_daily_attempts: int = 5
    daily_attempt_cap: int = 200
    ip_sessions_per_minute: int = 5
    ip_actions_per_minute: int = 30
    dev_login: str = "off"  # "on"이면 POST /api/v1/auth/dev/login 개방 — 2026-09-20 제출 뒤 .env에서 제거
    dev_account_id: str = ""
    dev_account_password: str = ""
    dev_login_per_minute: int = 5

    @property
    def auth_required(self) -> bool:
        """로그인을 요구하는가 — 정확히 `off`일 때만 우회하고 그 밖의 값(`on`·`On` 등)은 전부 켜진 것으로 본다.
        guards·기동 검사가 이 값 하나로 판정한다."""
        return self.guard_auth != "off"

    @property
    def public_deploy(self) -> bool:
        """공개 배포 설정인가 — 프론트 주소가 https면 공개로 본다(세션 쿠키 Secure 판정과 같은 기준).
        배포 설정에 따른 동작 차이는 main.deploy_profile이 이 값 하나로 고른다."""
        return self.frontend_base_url.startswith("https://")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
