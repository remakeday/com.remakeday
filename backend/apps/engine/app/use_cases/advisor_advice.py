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


def find_anchor(lead, observations):
    """플레이어 공개 관찰에서 anchor_cues 중 하나라도 text에 포함된 가장 최근(리스트 뒤쪽) 관찰을 찾는다."""
    for observation in reversed(list(observations)):
        if any(cue in observation.text for cue in lead.anchor_cues):
            return observation
    return None


def advice_sentence(lead, anchor) -> str:
    """닻이 되는 관찰과 함께 조언 문장을 조립한다."""
    head = f"네 기록의 「{anchor.text}」."
    if lead.ask:
        return f"{head} 내일 {lead.target}에게 {lead.ask} 물어봐라."
    return f"{head} {lead.target}: {lead.rule_action} 규칙을 걸어 봐라."
