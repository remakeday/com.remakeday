"""질문형 주장 판별 — 확인 화면에서 "단정해서 고쳐 보라"는 안내에만 쓴다 (테스터11 O2).

채점 입력은 바꾸지 않는다. 문장 끝 어미만 보므로 "왜 그런지 모르겠다" 같은 평서문은 거짓이다.
오표시보다 놓침이 낫다 — 물음표는 문장 끝에 있을 때만 보고(인용 대사 속 "배고파?"는 평서),
"누군가"류 부정대명사와 "편지·먼지" 같은 두 음절 "~ㄴ지" 어절은 질문으로 치지 않는다.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

_SENTENCE_RE = re.compile(r"(?<=[.!?？;…])\s+|\n+")
_TRAILING_RE = re.compile(r"[\s.!?？;:~…ㅋㅎㅠㅜ'\"”’)\]]+$")
_ENDING_QUESTION_MARK_RE = re.compile(r"[?？][?？!.~…;ㅋㅎㅠㅜ'\"”’)\]\s]*$")
_INDEFINITE_PRONOUNS = ("누군", "뭔", "언젠", "어딘", "무언")  # + "가" — 누군가·뭔가는 질문이 아니다

_JONG_N, _JONG_L, _JONG_BS, _JONG_SS, _JONG_B = 4, 8, 18, 20, 17


def _final_consonant(syllable: str) -> int | None:
    code = ord(syllable) - 0xAC00
    return code % 28 if 0 <= code < 11172 else None


@dataclass(frozen=True)
class _Ending:
    """어미 하나 — 마지막 음절과, 그 앞 음절이 만족해야 할 조건."""
    last: str
    before: Callable[[str], bool]

    def matches(self, core: str) -> bool:
        return len(core) >= 2 and core[-1] == self.last and self.before(core[:-1])


def _has_final(*finals: int) -> Callable[[str], bool]:
    return lambda head: _final_consonant(head[-1]) in finals


def _any_of(*rules: Callable[[str], bool]) -> Callable[[str], bool]:
    return lambda head: any(rule(head) for rule in rules)


def _all_of(*rules: Callable[[str], bool]) -> Callable[[str], bool]:
    return lambda head: all(rule(head) for rule in rules)


def _not_ending_with(*words: str) -> Callable[[str], bool]:
    return lambda head: not head.endswith(words)


def _last_word_at_least(syllables: int) -> Callable[[str], bool]:  # 마지막 어미 음절까지 세어 syllables 이상
    return lambda head: len(head.split()[-1]) + 1 >= syllables if head.split() else False


def _syllable_in(chars: str) -> Callable[[str], bool]:
    return lambda head: head[-1] in chars


def _formal_ni(head: str) -> bool:  # 습니까·ㅂ니까 — "아프니까"(이유)와 구분
    return len(head) >= 2 and head[-1] == "니" and _final_consonant(head[-2]) == _JONG_B


_ENDINGS = (
    _Ending("냐", lambda head: True),                                         # 끝나냐·뭐냐
    _Ending("까", _any_of(_has_final(_JONG_L), _formal_ni)),                  # 할까·일까·있습니까
    _Ending("가", _all_of(_any_of(_has_final(_JONG_N), _syllable_in("던")),   # 인가·는가·아픈가·건가
                          _not_ending_with(*_INDEFINITE_PRONOUNS))),          # 누군가·뭔가 제외
    _Ending("나", _any_of(_has_final(_JONG_SS, _JONG_BS), _syllable_in("프되"))),  # 했나·없나·아프나
    _Ending("니", _any_of(_has_final(_JONG_SS, _JONG_BS), _syllable_in("프되"))),  # 있니·아프니
    _Ending("지", _any_of(_all_of(_has_final(_JONG_N), _last_word_at_least(3)),  # 사람인지 — 편지·먼지·은지 제외
                          _has_final(_JONG_L), _syllable_in("는"))),            # 할지·하는지
)


def _is_question_sentence(sentence: str) -> bool:
    if _ENDING_QUESTION_MARK_RE.search(sentence):
        return True
    core = _TRAILING_RE.sub("", sentence)
    if core.endswith("요"):
        core = core[:-1]
    return any(ending.matches(core) for ending in _ENDINGS)


def is_question_claim(text: str) -> bool:
    return any(_is_question_sentence(s) for s in _SENTENCE_RE.split(text) if s.strip())
