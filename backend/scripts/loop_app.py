"""E7 Stage 4 전용 서버 조립 — 프로덕션 main.app에 러너의 thinking 제어만 주입한다.

프로덕션 엔진 코드는 수정하지 않는다 (model_evaluation.md §2.3·§4.2).
thinking 제어는 러너 서브클래스(ThinkingOllamaLLM)에만 있고, 이 모듈은
컴포지션 루트의 get_core_llm 바인딩만 러너 쪽 인스턴스로 바꿔치기한다.

실행 (Stage 4 러너가 서브프로세스로 띄운다):
    DATABASE_URL=...pigfarm_test CORE_LLM_PROVIDER=ollama CORE_LLM_MODEL=<후보> \
    .venv/bin/python -m uvicorn scripts.loop_app:app --port 8600

게이트 C9 검증용으로 /loop-debug 를 추가한다 — Core 콜 수·thinking 문자 수 누계.
"""

import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
for p in (str(_SCRIPTS), str(_SCRIPTS.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from run_core_selection import ThinkingOllamaLLM  # noqa: E402

from core.matrix.grid_keymaker_secret_manager import get_settings  # noqa: E402


class _CountingCoreLLM(ThinkingOllamaLLM):
    """think=False 강제 + 콜 수·thinking 사용량 누계 (게이트 C9 검증용)."""

    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        super().__init__(base_url=base_url, model=model, think=False, timeout=timeout)
        self.calls = 0
        self.thinking_chars_total = 0

    def complete(self, messages, json_schema, *, temperature=None) -> dict:
        try:
            return super().complete(messages, json_schema, temperature=temperature)
        finally:
            self.calls += 1
            self.thinking_chars_total += int(self.last.get("thinking_chars") or 0)


_core_singleton: _CountingCoreLLM | None = None


def _loop_core_llm() -> _CountingCoreLLM:
    global _core_singleton
    if _core_singleton is None:
        s = get_settings()
        if s.core_llm_provider != "ollama":
            raise RuntimeError(
                f"Stage 4 서버는 CORE_LLM_PROVIDER=ollama 로만 띄운다 (현재 {s.core_llm_provider})"
            )
        timeout = float(os.environ.get("LOOP_CORE_TIMEOUT", "300"))
        _core_singleton = _CountingCoreLLM(
            base_url=s.ollama_base_url, model=s.core_llm_model, timeout=timeout
        )
    return _core_singleton


# 컴포지션 루트 바인딩 교체 — engine_dependency는 get_core_llm을 이름으로 들고 있다
import apps.engine.dependencies.engine_dependency as _ed  # noqa: E402
import apps.engine.dependencies.llm_factory as _lf  # noqa: E402

_ed.get_core_llm = _loop_core_llm
_lf.get_core_llm = _loop_core_llm

from main import app  # noqa: E402


@app.get("/loop-debug")
def loop_debug():
    llm = _loop_core_llm()
    return {
        "core_model": llm._model,  # noqa: SLF001 — 러너 전용 디버그
        "think": "off",
        "core_calls": llm.calls,
        "thinking_chars_total": llm.thinking_chars_total,
    }
