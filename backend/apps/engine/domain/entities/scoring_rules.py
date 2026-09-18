"""채점·멸망 방식·판 종료 — 순수 함수 (기획서 §7.2, 모델정책 §5.4)."""

import re

from apps.engine.domain.value_objects.game_constants import (
    ANOMALY_CLOSURE,
    CELL_FULL_THRESHOLD,
    PASS_THRESHOLD,
    RUMOR_THRESHOLD,
    UNDERSTANDING_WEIGHTS,
)

_VERDICT_VALUE = {"confirmed": 1.0, "partial": 0.5, "none": 0.0}


REVEAL_THRESHOLD = 80.0  # 이 이해도(셀 기준)부터 결말에서 그 셀의 진실 줄이 열린다


def truth_reveal(truth_claims, per_truth: list[dict]) -> list[dict]:
    """스포일러 필터 — confirmed 명제만 진실 전문을 연다. partial·none은 서버가 잠근다."""
    by_code = {t.code: t for t in truth_claims}
    return [{
        "code": item["id"], "cell": by_code[item["id"]].cell,
        "verdict": item["verdict"], "my_claim": item.get("matched_user_claim"),
        "truth": by_code[item["id"]].text if item["verdict"] == "confirmed" else None,
    } for item in per_truth if item["id"] in by_code]


def cell_score(verdicts: list[str]) -> float:
    """칸 점수(%) — 확인 비율. 80% 이상 만점, 미만 비례."""
    if not verdicts:
        return 0.0
    ratio = sum(_VERDICT_VALUE[v] for v in verdicts) / len(verdicts)
    if ratio >= CELL_FULL_THRESHOLD:
        return 100.0
    return round(ratio / CELL_FULL_THRESHOLD * 100.0, 1)


def total_score(cell_scores: dict[str, float], *, include_side_effect: bool = False) -> float:
    """이해도: 상황 70(원인35·동기35) + 정체30. 기존 키워드는 호환용으로 무시한다."""
    return round(sum(cell_scores.get(c, 0.0) * weight
                     for c, weight in UNDERSTANDING_WEIGHTS.items()), 1)


def passed(total: float) -> bool:
    return total >= PASS_THRESHOLD


_CELL_LABELS = {
    "cause": "원인",
    "motive": "동기",
    "side_effect": "부작용",
    "identity": "정체",
}


def _with_topic_particle(word: str) -> str:
    """은/는 — 마지막 글자의 받침 유무로 고른다."""
    last = word[-1]
    has_final = (ord(last) - 0xAC00) % 28 != 0 if "가" <= last <= "힣" else False
    return word + ("은" if has_final else "는")


# 밤마다 이름을 꺼내는 칸 — 정체는 아무도 묻지 않는 질문이라 안내하지 않는다(기획서 §4.8⑤),
# 부작용은 채점하지 않는다.
HINT_CELLS = ("cause", "motive")


def cell_feedback(cell_scores: dict[str, float], *, include_side_effect: bool) -> str:
    """밤의 정성 피드백 — 점수는 숨기고 원인·동기의 진행만 문장으로.

    ≥80 "잡혔다" / >0 "조금 잡혔다". 점수 0인 칸은 empty_hint_cells()가 힌트로 넘긴다.
    """
    parts = []
    for cell in HINT_CELLS:
        score = cell_scores.get(cell, 0.0)
        if score <= 0.0:
            continue
        status = "잡혔다" if score >= 80.0 else "조금 잡혔다"
        parts.append(f"{_with_topic_particle(_CELL_LABELS[cell])} {status}.")
    return " ".join(parts)


def empty_hint_cells(cell_scores: dict[str, float]) -> list[str]:
    """점수 0인 칸 코드 — 힌트는 칸 이름만(테스터10 F1). 문구는 화면이 정한다."""
    return [cell for cell in HINT_CELLS if cell_scores.get(cell, 0.0) <= 0.0]


def world_outcome(anomaly_count: int, rumor_index: int) -> str:
    """멸망 방식 — 이상자 수·소문 지수 (Manager는 사유 문장만 만든다)."""
    if anomaly_count >= ANOMALY_CLOSURE:
        return "closure"
    if rumor_index >= RUMOR_THRESHOLD:
        return "quiet"
    return "truck"


def closed_by(total: float, *, identity_word_confirmed: bool) -> str:
    """판 종료 사유. 100%면 understood, 정체 단어 확인까지면 understood_all."""
    if total >= 100.0:
        return "understood_all" if identity_word_confirmed else "understood"
    if total >= PASS_THRESHOLD:
        return "clear"
    return "doom"


_VERDICT_RANK = {"none": 0, "partial": 1, "confirmed": 2}

_EDGE_PUNCT = ".!?…,\"'"


def _normalize_claim(text: str) -> str:
    return " ".join(text.split()).strip(_EDGE_PUNCT + " ")


def apply_ratchet(per_truth: list[dict], prev_per_truth: list[dict],
                  user_claims: list[str]) -> list[dict]:
    """단조 잠금 — 유저가 문장을 바꾸지 않았으면 판정은 나빠지지 않는다.

    직전 밤 같은 명제의 matched_user_claim 문장이 이번 후보에도 그대로 있으면
    직전 verdict 미만으로 내리지 않는다(confirmed→partial/none, partial→none 차단).
    상향은 그대로 둔다. 적용된 항목은 "ratcheted": True로 표시하고, matched_index는
    이번 후보에서 찾은 문장(같은 원문 우선, 없으면 정규화가 같은 첫 후보)을 가리킨다.
    """
    if not prev_per_truth:
        return per_truth
    prev_by_id = {p.get("id"): p for p in prev_per_truth}
    out = []
    for item in per_truth:
        prev = prev_by_id.get(item.get("id"))
        if prev:
            prev_match = prev.get("matched_user_claim")
            downgraded = (_VERDICT_RANK.get(item.get("verdict"), 0)
                          < _VERDICT_RANK.get(prev.get("verdict"), 0))
            index = _candidate_index(prev_match, user_claims) if prev_match else None
            if downgraded and index is not None:
                item = {**item, "verdict": prev["verdict"], "matched_user_claim": prev_match,
                        "matched_index": index, "ratcheted": True}
        out.append(item)
    return out


def _candidate_index(claim: str, candidates: list[str]) -> int | None:
    if claim in candidates:
        return candidates.index(claim)
    key = _normalize_claim(claim)
    return next((j for j, c in enumerate(candidates) if _normalize_claim(c) == key), None)


_QUOTE_MARKS = "\"'“”‘’「」『』"


def _squash(text: str) -> str:
    return "".join(text.split())


def _quote_key(quote: str) -> str:
    """인용 조각을 비교용으로 정리한다 — 공백 제거, 앞의 목록 번호("2. "), 양끝 따옴표·문장부호 제거."""
    key = _squash(quote)
    key = re.sub(r"^\d+\.", "", key)
    return key.strip(_QUOTE_MARKS + _EDGE_PUNCT)


def resolve_matched_index(candidates: list[str], quote: str | None, index: int | None) -> int | None:
    """채점기가 인용한 후보 문장 조각으로 matched_index를 보정한다.

    모델이 why·인용에서는 근거 문장을 맞게 짚으면서 번호는 하나 어긋나게 내는 사례가
    실판 181건 중 38건이었다(항상 인용 후보 − 1). 인용을 공백 제거 후 4자 이상이고
    정확히 한 후보에만 부분 문자열로 들어 있으면 그 후보의 번호를 index보다 우선한다.
    인용이 없거나 짧거나 0개·2개 이상 후보에 들어 있으면 index를 그대로 돌려준다.
    모델이 인용을 따옴표로 감싸거나 목록 번호를 함께 옮겨도 같은 후보로 본다.
    """
    key = _quote_key(quote or "")
    if len(key) < 4:
        return index
    hits = [j for j, c in enumerate(candidates) if key in _squash(c)]
    return hits[0] if len(hits) == 1 else index


_ACCEPTED_VERDICTS = frozenset({"confirmed", "partial"})


def accepted_claims(per_truth: list[dict], candidates: list[str]) -> list[str]:
    """인정된 내 문장 — 점수에 들어간 판정(잠금 포함)이 지목한 이번 밤 후보 원문.

    칸 구분 없이 플레이어가 쓴 순서로 낸다(진실 명제 순서·칸 구조를 드러내지 않는다).
    판정이 실제로 지목한 후보 인덱스(matched_index — 채점기 인덱스, 잠금이면 apply_ratchet이
    이번 후보에서 찾은 인덱스)만 쓴다. 문자열로 거르지 않으므로 정규화만 다른 근접 중복 후보는
    지목된 쪽만 보이고, 인덱스가 없는 지목(지난 기록 조각·어긋난 매칭)은 보정 없이 빠진다
    (테스터9 F11).
    """
    indices = {i["matched_index"] for i in per_truth
               if i.get("verdict") in _ACCEPTED_VERDICTS and i.get("matched_index") is not None}
    return [c for j, c in enumerate(candidates) if j in indices]
