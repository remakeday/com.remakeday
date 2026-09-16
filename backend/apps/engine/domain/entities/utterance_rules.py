"""플레이어 입력의 무의미 판정 — 모델 호출 전 규칙 게이트 (테스터6 F2)."""

import re

_SYLLABLE_RE = re.compile(r"[가-힣]")
_REPEAT_SYLLABLE_RE = re.compile(r"^([가-힣])\1{2,}$")  # 같은 음절 3회 이상만


def is_nonsense(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return True
    if not _SYLLABLE_RE.search(stripped):
        return True  # 완성 음절 0개: 자모·기호·점만
    if _REPEAT_SYLLABLE_RE.match(stripped):
        return True  # "왜왜왜왜", "아아아아"
    return False
