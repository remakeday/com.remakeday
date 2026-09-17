"""직접 쓴 규칙의 유한 문법 — 행동 활용형과 금지 표현 (테스터10 F3).

LLM이 뜻을 풀지 않는다. 행동 목록의 평서형("기록한다")에서 어간을 만들어
정해진 어미(기·는·지·게·고)만 받고, 금지 표현도 닫힌 목록으로만 읽는다.
남는 글자가 있으면 호출자가 거부한다 — 인식 범위를 넓혀도 뜻을 추측하지 않는다.
"""

import re
from dataclasses import dataclass

_HANGUL_BASE = 0xAC00
_FINAL_L = 8
_ENDINGS = "기|는|지|게|고"
_PARTICLES = "(?:을|를|에|이|가)?"

# 금지로 읽는 표현 — 긴 것부터. 어간+지 형태("기록하지")는 행동 쪽에서 먹고 뒤의 "않는다·못하게"만 여기 남는다.
SUPPRESS_RE = re.compile(
    r"못\s*하게|못한다|않는다|않기|않게|않도록|안\s*한다|안\s*하기|안\s*하게|포기한다|포기하기|포기|금지"
)


@dataclass(frozen=True)
class ActionMatch:
    action: str
    span: str
    negated: bool  # "기록 안 한다"처럼 행동 사이에 낀 부정


def _without_final(syllable: str, final: int = 0) -> str:
    code = ord(syllable) - _HANGUL_BASE
    return chr(_HANGUL_BASE + code - code % 28 + final)


def _verb_pattern(verb: str) -> str:
    """평서형 동사의 원형 또는 어간+어미. "…는다"는 앞을, "…ㄴ다"는 받침 ㄴ을 뗀 어간(ㄹ 탈락형도)을 쓴다."""
    if verb.endswith("는다"):
        stems = [verb[:-2]]
    else:
        stems = [verb[:-2] + _without_final(verb[-2]), verb[:-2] + _without_final(verb[-2], _FINAL_L)]
    return "(?:" + "|".join([re.escape(verb), *(f"{re.escape(s)}(?:{_ENDINGS})" for s in stems)]) + ")"


def _action_pattern(action: str) -> re.Pattern:
    *heads, verb = action.split()
    noun_verb = verb.endswith("한다") and len(verb) > 2
    if noun_verb:  # "기록한다" → "기록" + "한다": "기록을 안 한다"·"기록 금지"도 받는다
        heads, verb = [*heads, verb[:-2]], "한다"
    head = r"\s*".join(re.escape(re.sub("[을를에]$", "", word)) + _PARTICLES for word in heads)
    verb_part = rf"(?P<neg>(?:안|못)\s*)?{_verb_pattern(verb)}"
    if noun_verb:
        verb_part = rf"(?:{verb_part}|(?=\s*(?:포기|금지)))"
    return re.compile((head + r"\s*" if heads else "") + verb_part)


def find_actions(text: str, vocab: list[str]) -> list[ActionMatch]:
    matches = []
    for action in vocab:
        found = _action_pattern(action).search(text)
        if found:
            matches.append(ActionMatch(action, found.group(0), bool(found.group("neg"))))
    return matches


def wants_suppress(text: str) -> bool:
    """대안을 금지형으로 줄지 — 금지 표현이 정확히 하나일 때만. 겹친 부정은 뜻을 정하지 않는다."""
    return len(SUPPRESS_RE.findall(text)) == 1
