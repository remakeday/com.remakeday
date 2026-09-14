"""E6 후속 루프 스모크 전용 서버 조립 — loop_app.py의 확장.

프로덕션 main.app에 러너의 thinking 제어를 Core와 NPC 양쪽에 주입한다.
프로덕션 엔진 코드·.env는 수정하지 않는다 (loop_app.py와 같은 원칙).

- Core: CORE_LLM_PROVIDER=ollama 필수 → ThinkingOllamaLLM(think=False)
- NPC:  NPC_LLM_PROVIDER=ollama 이고 모델 capabilities에 thinking이 있으면
        ThinkingOllamaLLM(think=False)로 교체 (qwen3.5 계열). 없으면(exaone) 프로덕션 그대로.

실행:
    DATABASE_URL=...pigfarm_test CORE_LLM_PROVIDER=ollama CORE_LLM_MODEL=gemma4:12b \
    NPC_LLM_MODEL=qwen3.5:4b \
    .venv/bin/python -m uvicorn scripts.loop_app_npc:app --port 8600

/loop-debug 는 Core·NPC 각각의 콜 수·thinking 문자 누계를 반환한다.
"""

import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
for p in (str(_SCRIPTS), str(_SCRIPTS.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import httpx  # noqa: E402
from run_core_selection import ThinkingOllamaLLM  # noqa: E402

from core.matrix.grid_keymaker_secret_manager import get_settings  # noqa: E402


class _CountingLLM(ThinkingOllamaLLM):
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


_core: _CountingLLM | None = None
_npc = None
_npc_counting = False


def _loop_core_llm():
    global _core
    if _core is None:
        s = get_settings()
        if s.core_llm_provider != "ollama":
            raise RuntimeError(f"CORE_LLM_PROVIDER=ollama 필요 (현재 {s.core_llm_provider})")
        _core = _CountingLLM(s.ollama_base_url, s.core_llm_model,
                             float(os.environ.get("LOOP_CORE_TIMEOUT", "300")))
    return _core


def _has_thinking(base_url: str, model: str) -> bool:
    try:
        res = httpx.post(f"{base_url.rstrip('/')}/api/show", json={"model": model}, timeout=10.0)
        return "thinking" in res.json().get("capabilities", [])
    except Exception:  # noqa: BLE001
        return False


def _loop_npc_llm():
    global _npc, _npc_counting
    if _npc is None:
        s = get_settings()
        if s.npc_llm_provider == "ollama" and _has_thinking(s.ollama_base_url, s.npc_llm_model):
            _npc = _CountingLLM(s.ollama_base_url, s.npc_llm_model,
                                float(os.environ.get("LOOP_NPC_TIMEOUT", "120")))
            _npc_counting = True
        else:
            import apps.engine.dependencies.llm_factory as lf
            _npc = lf.build_llm(s.npc_llm_provider, s.npc_llm_model, s.ollama_base_url)
    return _npc


import apps.engine.dependencies.engine_dependency as _ed  # noqa: E402
import apps.engine.dependencies.llm_factory as _lf  # noqa: E402

_ed.get_core_llm = _loop_core_llm
_lf.get_core_llm = _loop_core_llm
_ed.get_npc_llm = _loop_npc_llm
_lf.get_npc_llm = _loop_npc_llm

from main import app  # noqa: E402


@app.get("/loop-debug")
def loop_debug():
    core = _loop_core_llm()
    npc = _loop_npc_llm()
    out = {
        "core_model": core._model, "core_calls": core.calls,  # noqa: SLF001
        "core_thinking_chars": core.thinking_chars_total,
        "npc_model": getattr(npc, "_model", type(npc).__name__),
        "npc_think_forced_off": _npc_counting,
    }
    if _npc_counting:
        out["npc_calls"] = npc.calls
        out["npc_thinking_chars"] = npc.thinking_chars_total
    return out
