"""채점·멸망 방식·판 종료 — 순수 함수 (기획서 §7.2, 모델정책 §5.4)."""

from apps.engine.domain.value_objects.game_constants import (
    ANOMALY_CLOSURE,
    CELL_FULL_THRESHOLD,
    CELLS,
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


def cell_feedback(cell_scores: dict[str, float], *, include_side_effect: bool) -> str:
    """밤의 정성 피드백 — 점수는 숨기고 3단계 상태만 문장으로.

    ≥80 "잡혔다" / >0 "조금 잡혔다" / 0 "비어 있다". 부작용은 답안에서 제외한다.
    """
    parts = []
    for cell in CELLS:
        if cell == "side_effect":
            continue
        score = cell_scores.get(cell, 0.0)
        if score >= 80.0:
            status = "잡혔다"
        elif score > 0.0:
            status = "조금 잡혔다"
        else:
            status = "비어 있다"
        parts.append(f"{_with_topic_particle(_CELL_LABELS[cell])} {status}.")
    return " ".join(parts)


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
    상향은 그대로 둔다. 적용된 항목은 "ratcheted": True로 표시한다.
    """
    if not prev_per_truth:
        return per_truth
    prev_by_id = {p.get("id"): p for p in prev_per_truth}
    current = {_normalize_claim(c) for c in user_claims}
    out = []
    for item in per_truth:
        prev = prev_by_id.get(item.get("id"))
        if prev:
            prev_match = prev.get("matched_user_claim")
            downgraded = (_VERDICT_RANK.get(item.get("verdict"), 0)
                          < _VERDICT_RANK.get(prev.get("verdict"), 0))
            if prev_match and downgraded and _normalize_claim(prev_match) in current:
                item = {**item, "verdict": prev["verdict"],
                        "matched_user_claim": prev_match, "ratcheted": True}
        out.append(item)
    return out
