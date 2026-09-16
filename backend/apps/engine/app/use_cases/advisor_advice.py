"""신의 질문 답변 조립 — 판정·조언은 결정론, 진실은 모른다 (기획서 5.5·5.6)."""

import re

_WHY_CUES = ("왜", "이유", "어떻게", "어째서", "뭐 때문")
_POLITE_RE = re.compile(r"(습니다|합니다|입니다)")
_CONFIRM_RE = re.compile(r"확인(했|됐|되었|하였)")

WHY_PREFIX = "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."
_VERDICT = {"supported": "맞다.", "contradicted": "아니다.", "unknown": "그건 알 수 없다."}


def is_why_question(text: str) -> bool:
    return any(cue in text for cue in _WHY_CUES)


def verdict_prefix(status: str, why: bool) -> str:
    if why:
        return WHY_PREFIX
    return _VERDICT.get(status, _VERDICT["unknown"])


def polite_register_check(out) -> str | None:
    if _POLITE_RE.search(str(getattr(out, "answer", "") or "")):
        return "register: 합니다체"
    return None


def unbacked_confirmation_check(out) -> str | None:
    answer = str(getattr(out, "answer", "") or "")
    if _CONFIRM_RE.search(answer) and not list(getattr(out, "evidence", []) or []):
        return "unbacked_confirmation"
    return None
