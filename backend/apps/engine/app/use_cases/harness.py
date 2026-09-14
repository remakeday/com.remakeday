"""시스템 하네스 — 프롬프트가 아니라 코드 (모델정책 §9).

검사 순서: 1 JSON 파싱 → 2 스키마 → 3~5·7 사실 층(가변 체크) → 실패 시 재생성(최대 2회) → 폴백.
SYSTEM_HARNESS=off는 사실 층(fact_checks)만 끈다. 파싱·스키마는 항상 켠다.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar
from time import perf_counter

from pydantic import BaseModel, ValidationError

from apps.engine.app.ports.output.llm_port import LLMParseError, LLMPort, MessageDTO

MAX_REGENERATIONS = 2

T = TypeVar("T", bound=BaseModel)

# 체크: 검증된 출력 모델을 받아 위반 사유(str) 또는 None 반환
FactCheck = Callable[[BaseModel], str | None]


@dataclass
class HarnessReport:
    role: str
    attempts: int = 0
    violations: list[str] = field(default_factory=list)
    fallback_used: bool = False
    call_records: list[dict] = field(default_factory=list)
    model: str | None = None


def run_with_harness(
    llm: LLMPort,
    messages: list[MessageDTO],
    output_model: type[T],
    *,
    role: str,
    fact_checks: list[FactCheck] | None = None,
    harness_on: bool = True,
    temperature: float | None = None,
    retry_feedback: bool = False,
) -> tuple[T | None, HarnessReport]:
    """통과한 출력 또는 (None, report) — None이면 호출자가 역할별 폴백을 적용한다."""
    report = HarnessReport(role=role, model=getattr(llm, "_model", type(llm).__name__))
    checks = fact_checks or []
    schema = output_model.model_json_schema()
    messages = list(messages)

    def explain_retry(error):
        if retry_feedback and report.attempts <= MAX_REGENERATIONS:
            messages.append(MessageDTO(role="user", content=(
                "이전 출력의 검증 오류: " + error + ". 위 입력과 출력 스키마를 다시 확인하고 이 오류를 수정한 JSON을 반환하라.")))

    for _ in range(1 + MAX_REGENERATIONS):
        report.attempts += 1
        started = perf_counter()
        record = {"attempt": report.attempts, "messages": [m.model_dump() for m in messages],
                  "output": None, "checks": [], "accepted": False, "temperature": temperature}
        report.call_records.append(record)
        try:
            raw = llm.complete(list(messages), schema, temperature=temperature)
        except LLMParseError as exc:
            report.violations.append(f"parse: {exc}")
            record.update(error=f"parse: {exc}", elapsed_ms=round((perf_counter() - started) * 1000))
            explain_retry(f"parse: {exc}")
            continue
        except Exception as exc:
            # Provider/network failures are boundary outcomes, not lost batches.
            # Stop this call instead of retrying an unavailable provider; siblings can still finish.
            error = f"provider: {type(exc).__name__}: {exc}"
            record.update(error=error, elapsed_ms=round((perf_counter() - started) * 1000))
            report.violations.append(error)
            report.fallback_used = True
            return None, report
        record.update(output=raw, elapsed_ms=round((perf_counter() - started) * 1000))
        try:
            parsed = output_model.model_validate(raw)
        except ValidationError as exc:
            report.violations.append(f"schema: {exc.errors()[:2]}")
            record["checks"].append(report.violations[-1])
            explain_retry(report.violations[-1])
            continue
        if harness_on:
            failed = next((v for c in checks if (v := c(parsed)) is not None), None)
            if failed is not None:
                report.violations.append(failed)
                record["checks"].append(failed)
                explain_retry(failed)
                continue
        record["accepted"] = True
        return parsed, report

    report.fallback_used = True
    return None, report


def forbidden_word_check(words: list[str], *, fields: list[str]) -> FactCheck:
    """검사 4 — 자연어 필드의 금칙어."""

    def check(output: BaseModel) -> str | None:
        for f in fields:
            text = getattr(output, f, None) or ""
            for w in words:
                if w and w in str(text):
                    return f"forbidden_word: '{w}' in {f}"
        return None

    return check


def lost_character_check(lost_names: list[str], *, fields: list[str]) -> FactCheck:
    """검사 5 — 소실 인물 언급 (damage_level 3 이후)."""

    def check(output: BaseModel) -> str | None:
        for f in fields:
            text = getattr(output, f, None) or ""
            for name in lost_names:
                if name and name in str(text):
                    return f"lost_character: '{name}' in {f}"
        return None

    return check


import re

# "X야/X이야/X예요"(명명), "X가 그랬/말했"(전언) — 사람을 지목하는 어법의 후보 토큰
_NAMING_RE = re.compile(r"([가-힣]{2,3})(?:이?야[.!?\s]|예요|이에요|[이가]\s*(?:그랬|말했|했다던))")
# 명명 어법에 자주 붙는 비인명 어휘 — 오탐 방지
_NOT_NAMES = {
    "차량", "번호", "알려", "뜻이",
    "소문", "일이", "내용", "기억", "기록", "사실", "이유", "모양", "소리", "차례", "숫자", "이름", "걱정", "규칙", "순서", "상태", "표시", "문제", "담요", "수첩",
    "아니", "몰라", "때문", "얘기", "진짜", "정말", "그거", "이거", "저거", "그것",
    "이것", "저것", "무엇", "누구", "여기", "저기", "거기", "지금", "오늘", "내일",
    "어제", "사람", "우리", "혼자", "전부", "하나", "생각", "기분", "마음", "정도",
    "처음", "마지막", "배급", "검진", "방송", "트럭", "구역", "바깥", "그냥",
}


def unknown_person_check(known_names: list[str], *, fields: list[str]) -> FactCheck:
    """검사 5' — 없는 인물 언급 (기획서 8.6). 명부 밖 이름을 지어내면 거부."""

    def check(output: BaseModel) -> str | None:
        for f in fields:
            text = str(getattr(output, f, None) or "")
            for cand in _NAMING_RE.findall(text):
                stem = cand[:-1] if cand.endswith("이") and len(cand) > 2 else cand
                if cand in _NOT_NAMES or stem in _NOT_NAMES:
                    continue
                if any(
                    c in name or name in c
                    for name in known_names
                    for c in (cand, stem)
                ):
                    continue
                return f"unknown_person: '{stem}' in {f}"
        return None

    return check


# 영문 단어(2자 이상)·한글 문자 — 언어 전환 판정용
_ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{2,}")
_HANGUL_RE = re.compile(r"[가-힣]")


def korean_only_check(*, fields: list[str]) -> FactCheck:
    """검사 4' — 언어 가드. 영어로 전환한 발화는 거부한다.

    영문 단어([A-Za-z]{2,})가 2개 이상이거나, 영문 단어가 있는데 한글이 0이면 위반.
    짧은 감탄·고유명 1개는 관용 (한글이 함께 있을 때).
    """

    def check(output: BaseModel) -> str | None:
        for f in fields:
            text = str(getattr(output, f, None) or "")
            words = _ENGLISH_WORD_RE.findall(text)
            if len(words) >= 2 or (words and _HANGUL_RE.search(text) is None):
                return f"korean_only: {words[:3]} in {f}"
        return None

    return check


def action_vocab_check(vocab: list[str], *, getter: Callable[[BaseModel], list[str]]) -> FactCheck:
    """검사 3 — 행동 어휘 밖의 action."""

    def check(output: BaseModel) -> str | None:
        for action in getter(output):
            if action not in vocab:
                return f"action_vocab: '{action}'"
        return None

    return check
