"""P6 검증 러너 공용 모듈 — 모델 벤치마크·게임 밸런스 계측 (작업지시서 §P6).

모든 러너는 backend 루트에서 실행한다:
    .venv/bin/python scripts/run_xxx.py --help

결과는 docs/metrics.yml에 yaml flow-dict 한 줄 append + 콘솔 마크다운 표.
engine 코드는 수정하지 않는다 — import만 한다.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Literal

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402

from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM  # noqa: E402
from apps.engine.app.ports.output.llm_port import MessageDTO  # noqa: E402
from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402

DEFAULT_NPC_MODEL = "exaone3.5:7.8b"
DEFAULT_JUDGE_MODEL = "gemma4:12b"
DEFAULT_OUT = "docs/metrics.yml"  # 프로젝트 루트 기준 (= backend/../docs/metrics.yml)
SELFPLAY_ATTEMPTS_LOG = BACKEND_ROOT / "scripts" / ".selfplay_attempts.log"


# ── .env ──────────────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    """backend/.env를 읽는다. os.environ이 우선한다."""
    env: dict[str, str] = {}
    env_file = BACKEND_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k in env or k.startswith(("OLLAMA_", "INSPECTOR_"))})
    return env


def ollama_base_url() -> str:
    return load_env().get("OLLAMA_BASE_URL", "http://localhost:11434")


# ── ollama ────────────────────────────────────────────────────────────

def check_ollama(base_url: str, models: list[str]) -> None:
    """ollama 생존 + 모델 존재 확인. 안 떠 있으면 명확히 죽는다."""
    try:
        res = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
        res.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"[에러] ollama가 응답하지 않는다: {base_url} ({exc})\n"
            "       `ollama serve`가 떠 있는지, OLLAMA_BASE_URL이 맞는지 확인."
        ) from exc
    available = {m["name"] for m in res.json().get("models", [])}
    for m in models:
        if m not in available:
            raise SystemExit(
                f"[에러] ollama에 모델이 없다: {m}\n"
                f"       설치된 모델: {sorted(available)}\n"
                f"       `ollama pull {m}` 후 재시도."
            )


def make_llm(model: str, base_url: str | None = None, think: bool | None = False) -> OllamaLLM:
    """think 기본값 off — gemma4:12b는 thinking 모델이라 켜두면 판정 1건에 30초+ 걸린다.
    thinking 미지원 모델(exaone3.5, kanana1.5, gemma3)은 think 필드가 무시된다(무해)."""
    return OllamaLLM(base_url=base_url or ollama_base_url(), model=model, think=think)


def make_provider_llm(provider: str, model: str, base_url: str | None = None, think: bool | None = False):
    """provider별 LLM 빌더. ollama는 make_llm과 동일하고, anthropic은 프로덕션 팩토리
    (llm_factory.build_llm)를 그대로 쓴다 — run_core_selection·run_age7_check와 같은 경로.
    anthropic은 thinking 제어가 없어 think를 무시한다(키는 .env ANTHROPIC_API_KEY)."""
    if provider == "anthropic":
        # --model 기본값은 ollama 모델명이라 그대로 넘기면 Anthropic 404가 조용히 0점으로 집계된다(2026-09-18 실수).
        if not model.startswith("claude-"):
            raise SystemExit(f"[에러] --provider anthropic 에는 --model claude-… 를 함께 주세요 (받은 값: {model})")
        from apps.engine.dependencies.llm_factory import build_llm  # 지연 import — ollama 러너엔 영향 없음
        return build_llm("anthropic", model, base_url or ollama_base_url())
    if provider == "ollama":
        return make_llm(model, base_url, think)
    raise SystemExit(f"[에러] 알 수 없는 provider: {provider} (ollama/anthropic)")


def sys_msg(content: str) -> MessageDTO:
    return MessageDTO(role="system", content=content)


def usr_msg(content: str) -> MessageDTO:
    return MessageDTO(role="user", content=content)


# ── LLM-as-judge ──────────────────────────────────────────────────────

class JudgeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Literal["PASS", "FAIL"]
    why: str = ""


def judge_pass(judge_llm: OllamaLLM, judge_system: str, material: str) -> tuple[bool | None, str]:
    """gemma 판정. (판정 or None, 사유). None = 판정 자체가 실패(파싱 불가)."""
    out, _report = run_with_harness(
        judge_llm,
        [sys_msg(judge_system), usr_msg(material)],
        JudgeOutput,
        role="judge",
    )
    if out is None:
        return None, "judge 출력 파싱 실패"
    return out.verdict == "PASS", out.why


# ── metrics.yml append ───────────────────────────────────────────────

def resolve_out(out: str) -> Path:
    p = Path(out)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def _round(v):
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_round(x) for x in v]
    return v


def append_metric(out: str, runner: str, model: str, **fields) -> Path:
    """`- {runner: ..., date: ..., model: ..., ...}` 한 줄 append.

    JSON flow-dict는 유효한 YAML이다. 한글은 ensure_ascii=False로 그대로 둔다.
    """
    row = {"runner": runner, "date": date.today().isoformat(), "model": model}
    row.update(_round(fields))
    path = resolve_out(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("- " + json.dumps(row, ensure_ascii=False) + "\n")
    return path


# ── 콘솔 마크다운 표 ─────────────────────────────────────────────────

def print_table(headers: list[str], rows: list[list]) -> None:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)

    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        print("| " + " | ".join(fmt(v) for v in r) + " |")


def add_common_args(parser, *, default_model: str = DEFAULT_NPC_MODEL, default_n: int = 4) -> None:
    parser.add_argument("--model", default=default_model, help=f"대상 모델 (기본 {default_model})")
    parser.add_argument("--n", type=int, default=default_n, help=f"반복 수 (기본 {default_n})")
    parser.add_argument("--out", default=DEFAULT_OUT, help="metrics 파일 (프로젝트 루트 기준, 기본 docs/metrics.yml)")
    parser.add_argument("--base-url", dest="ollama_url", default=None, help="ollama base url (기본 .env OLLAMA_BASE_URL)")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help=f"판정 모델 (기본 {DEFAULT_JUDGE_MODEL})")
