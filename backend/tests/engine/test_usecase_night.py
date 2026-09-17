"""밤 채점 — 주장 매칭(인덱스 기반)·원인 체인 입력 필터 (FakeLLM 큐로 제어)."""

import json
import uuid
from types import SimpleNamespace

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.use_cases.night_interactor import (
    NightInteractor,
    chain_source_events,
)
from apps.engine.domain.value_objects.event_type import EventType


class _RecorderEvents:
    def __init__(self):
        self.recorded = []

    def record(self, session_id, event):
        self.recorded.append(event)


def make_night_judge(core_queue):
    events = _RecorderEvents()
    interactor = NightInteractor(
        attempts=None, loops=None, notes=None, rules=None, nights=None,
        event_log=events, scenario=None, core_llm=FakeLLM(core_queue),
        harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    return interactor, events


_LOOP = SimpleNamespace(attempt_id=uuid.uuid4(), loop_n=1)
_TRUTH = [SimpleNamespace(
    code="cause-1", cell="cause", text="채연이 아프다", is_identity_word=False,
)]


def draft_result(source, notes=()):
    loop = SimpleNamespace(
        id=uuid.uuid4(), attempt_id=uuid.uuid4(), loop_n=1, state="night_pending",
    )
    saved = []
    interactor = NightInteractor(
        attempts=None, loops=SimpleNamespace(get=lambda _: loop, save=lambda: None),
        notes=None,  # draft는 노트 원문을 읽지 않는다 — 고른 id만 기록
        rules=None, nights=SimpleNamespace(for_loop=lambda _: None, create=saved.append),
        event_log=_RecorderEvents(), scenario=None,
        core_llm=FakeLLM([{"claims": ["채연은 아픈 것을 숨겼다."]}]),
        harness_on=True, cookie_ab_on=False,
        night_cls=lambda **kw: SimpleNamespace(id=uuid.uuid4(), **kw),
    )
    result = interactor.draft(loop.id, list(range(len(notes))), source)
    return result, saved[0]


def draft_answer(source, notes=()):
    result, night = draft_result(source, notes)
    return result["claims"], night


@pytest.mark.parametrize("source", [
    "채연은 열이 나서 아프다. 채연은 이송될까 봐 아픈 것을 숨겼다.",
    "채연은 열이 나서 아프다.\n채연은 이송될까 봐 아픈 것을 숨겼다.",
])
def test_draft_preserves_illness_and_motive_across_line_breaks(source):
    claims, _ = draft_answer(source)
    assert claims == ["채연은 열이 나서 아프다.", "채연은 이송될까 봐 아픈 것을 숨겼다."]


def test_draft_keeps_facts_after_eighth_sentence():
    source = "하나. 둘. 셋. 넷. 다섯. 여섯. 일곱. 여덟. 아홉. 우리는 돼지다."
    claims, _ = draft_answer(source)
    assert claims == ["하나.", "둘.", "셋.", "넷.", "다섯.", "여섯.", "일곱.", "여덟. 아홉. 우리는 돼지다."]


def test_selected_notes_without_free_text_make_no_claims():
    # 기록은 참고 목록일 뿐 채점 후보가 아니다 (테스터9 F17·테스터11 O1)
    claims, night = draft_answer("", ["소독약 냄새.", "트럭 소리."])
    assert claims == []
    assert night.tapped_note_ids == [0, 1]  # 표시 상태는 다음 밤 복원용으로 남는다


def test_selected_notes_are_not_appended_to_written_claims():
    claims, _ = draft_answer("하나. 둘. 셋. 넷. 다섯. 여섯. 일곱. 여덟.", ["관리자는 다른 종이다."])
    assert claims[-1] == "여덟."
    assert all("관리자는 다른 종이다" not in c for c in claims)


def test_draft_flags_question_claims_in_claim_order():
    result, _ = draft_result("채연은 아프다. 밥이 문제인가;;;\n왜 그런지 모르겠다", ["트럭 소리?"])
    assert result["claims"] == ["채연은 아프다.", "밥이 문제인가;;;", "왜 그런지 모르겠다"]
    assert result["is_question"] == [False, True, False]


def test_edit_claims_returns_question_flags():
    loop = SimpleNamespace(attempt_id=uuid.uuid4(), loop_n=1)
    night = SimpleNamespace(id=uuid.uuid4(), loop_id=uuid.uuid4(), claims=["채연은 아픈가?"],
                            edit_count=0, submitted=False, user_edited=False)
    interactor = NightInteractor(
        attempts=None, loops=SimpleNamespace(get=lambda _: loop), notes=None, rules=None,
        nights=SimpleNamespace(get=lambda _: night, save=lambda: None),
        event_log=_RecorderEvents(), scenario=None, core_llm=None,
        harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    result = interactor.edit_claims(night.id, ["채연은 아프다.", "왜 숨겼을까"])
    assert result == {"claims": ["채연은 아프다.", "왜 숨겼을까"], "is_question": [False, True]}


@pytest.mark.parametrize("source", [
    "우리는 돼지가 아니다. 아마 사람인 것 같다.",
    "체온은 38.5도다. 채연은 열이 없다고 했다.",
    "채연은 이송될까 봐 아픈 것을 숨겼고 그래서 검진에서 열을 발견하지 못했다",
    "나는 무서웠다! 왜 이럴까?",
])
def test_draft_does_not_rewrite_negation_uncertainty_numbers_or_causal_links(source):
    claims, night = draft_answer(source)
    assert " ".join(claims) == source
    assert night.fabricated_dropped == []


def test_empty_draft_does_not_invent_claims():
    claims, _ = draft_answer(" \n ")
    assert claims == []


def test_matched_index_excludes_claim_from_wrong():
    interactor, _ = make_night_judge(
        [{"verdict": "confirmed", "matched_index": 0, "why": ""}]
    )
    claims = ["채연이 아픈 것 같다", "민석이 방송실 갔다"]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "confirmed"
    assert per_truth[0]["matched_user_claim"] == "채연이 아픈 것 같다"
    assert wrong == ["민석이 방송실 갔다"]


def test_judge_renders_all_user_claims_as_candidates():
    # 유저 주장은 최대 8개 — top3로 자르지 않고 전부 후보로 넣는다
    interactor, _ = make_night_judge(
        [{"verdict": "confirmed", "matched_index": 4, "why": ""}]
    )
    claims = [
        "민석이 방송실 갔다", "은상이 소문을 냈다", "배급이 늦게 나왔다",
        "준이 손목띠를 봤다", "채연이 아픈 것 같다",
    ]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "confirmed"
    assert per_truth[0]["matched_user_claim"] == "채연이 아픈 것 같다"
    assert per_truth[0]["cited"] == claims  # 후보 전수
    assert "채연이 아픈 것 같다" not in wrong


def test_out_of_range_index_regenerates_then_falls_back():
    bad = {"verdict": "confirmed", "matched_index": 7, "why": ""}
    interactor, events = make_night_judge([bad, bad, bad])
    claims = ["채연이 아픈 것 같다"]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "none"
    assert per_truth[0]["matched_user_claim"] is None
    assert wrong == claims
    # 범위 밖 인덱스는 하네스에서 거부돼야 한다.
    assert any(
        "matched_index" in v for e in events.recorded for v in e.violations
    )


@pytest.mark.parametrize(("claims", "expected"), [
    (["채연이 아프다 채연이 숨겼다 우리는 돼지다"], [{"const": 0, "type": "integer"}, {"type": "null"}]),
    (["채연이 아프다", "채연이 숨겼다", "우리는 돼지다"], [{"enum": [0, 1, 2], "type": "integer"}, {"type": "null"}]),
])
def test_judge_exposes_only_existing_candidate_indices_to_model(claims, expected):
    interactor, _ = make_night_judge([{"verdict": "confirmed", "matched_index": 0}])
    interactor._judge(_LOOP, _TRUTH, [], claims)
    schema = interactor._llm.calls[0][1]
    # 후보 안의 절 번호(2, 5, 7)를 만들어 내던 실제 모델 응답 재현.
    choices = schema["properties"]["matched_index"]["anyOf"]
    assert choices == expected


# ── 채점 신뢰 — temperature 0·후보 분할·단조 잠금 (2026-09-14 실판 da38de28) ──

from apps.engine.app.use_cases.night_interactor import judge_candidates  # noqa: E402
from apps.engine.domain.entities.scoring_rules import apply_ratchet  # noqa: E402


def test_judge_calls_evaluator_with_temperature_zero():
    # 회귀 고정 — 같은 제출은 같은 조건으로 판정한다
    interactor, _ = make_night_judge([{"verdict": "confirmed", "matched_index": 0}])
    interactor._judge(_LOOP, _TRUTH, [], ["채연이 아픈 것 같다"])
    assert interactor._llm.temperatures == [0.0]


def test_judge_candidates_splits_blob_cell_into_sentences():
    claims = ["하나.", "둘.", "셋.", "넷.", "다섯.", "여섯.", "일곱.", "여덟. 아홉. 우리는 돼지다."]
    assert judge_candidates(claims) == [
        "하나.", "둘.", "셋.", "넷.", "다섯.", "여섯.", "일곱.", "여덟.", "아홉.", "우리는 돼지다.",
    ]


def test_judge_candidates_dedupes_and_keeps_plain_cells():
    assert judge_candidates(["채연이 아프다.", "채연이 아프다.", "트럭 소리."]) == [
        "채연이 아프다.", "트럭 소리.",
    ]


def test_ratchet_blocks_confirmed_downgrade_when_sentence_unchanged():
    prev = [{"id": "identity-1", "verdict": "confirmed", "matched_user_claim": "이들은 동물이야."}]
    cur = [{"id": "identity-1", "verdict": "none", "matched_user_claim": None, "cited": []}]
    out = apply_ratchet(cur, prev, ["이들은 동물이야.", "채연이 아프다."])
    assert out[0]["verdict"] == "confirmed"
    assert out[0]["matched_user_claim"] == "이들은 동물이야."
    assert out[0]["ratcheted"] is True


def test_ratchet_blocks_partial_to_none():
    prev = [{"id": "cause-1", "verdict": "partial", "matched_user_claim": "채연이 아프다"}]
    cur = [{"id": "cause-1", "verdict": "none", "matched_user_claim": None, "cited": []}]
    out = apply_ratchet(cur, prev, ["채연이 아프다"])
    assert out[0]["verdict"] == "partial"
    assert out[0]["ratcheted"] is True


def test_ratchet_allows_upgrade_without_marking():
    prev = [{"id": "cause-1", "verdict": "none", "matched_user_claim": None}]
    cur = [{"id": "cause-1", "verdict": "confirmed", "matched_user_claim": "채연이 아프다", "cited": []}]
    out = apply_ratchet(cur, prev, ["채연이 아프다"])
    assert out[0]["verdict"] == "confirmed"
    assert "ratcheted" not in out[0]


def test_ratchet_skips_when_sentence_removed():
    prev = [{"id": "identity-1", "verdict": "confirmed", "matched_user_claim": "이들은 동물이야."}]
    cur = [{"id": "identity-1", "verdict": "none", "matched_user_claim": None, "cited": []}]
    out = apply_ratchet(cur, prev, ["이들은 사람이야."])
    assert out[0]["verdict"] == "none"
    assert "ratcheted" not in out[0]


def test_ratchet_normalizes_whitespace_and_edge_punctuation():
    prev = [{"id": "cause-1", "verdict": "confirmed", "matched_user_claim": "채연이  아프다."}]
    cur = [{"id": "cause-1", "verdict": "none", "matched_user_claim": None, "cited": []}]
    out = apply_ratchet(cur, prev, ["채연이 아프다"])
    assert out[0]["verdict"] == "confirmed"


def _submit_env(judge_queue, prev_per_truth, claims=None, truths=None):
    loop = SimpleNamespace(
        id=uuid.uuid4(), attempt_id=uuid.uuid4(), loop_n=2, state="night_draft",
        rumor_index=0, score=None, anomaly_count=0, side_effect_claims=None,
        cause_chain=None, world_outcome=None,
    )
    night = SimpleNamespace(
        id=uuid.uuid4(), loop_id=loop.id, submitted=False,
        claims=claims or ["이송된 애들은 동물이야. 그래서 우리도 동물이야."],
        free_text="", tapped_note_ids=[], per_truth_claim=None,
        cell_scores=None, total=None, passed=None,
    )
    prev_night = SimpleNamespace(per_truth_claim=prev_per_truth)
    events = _RecorderEvents()
    events.query = lambda *a, **k: []
    scenario = SimpleNamespace(
        truth_claims=lambda: truths or [SimpleNamespace(
            code="identity-1", cell="identity", text="이들은 동물이다",
            is_identity_word=True, world_outcomes=[],
        )],
        bundle=lambda: SimpleNamespace(fragments=[], ending_lines=[], ending_outcomes={}),
        beats=lambda: [SimpleNamespace(beat=6)],
    )
    interactor = NightInteractor(
        attempts=SimpleNamespace(get=lambda _: SimpleNamespace(status="active"), save=lambda: None),
        loops=SimpleNamespace(get=lambda _: loop, save=lambda: None, npc_states=lambda _: []),
        notes=SimpleNamespace(upsert=lambda *a, **k: None), rules=None,
        nights=SimpleNamespace(get=lambda _: night, save=lambda: None,
                               previous_submitted=lambda a, n: (prev_night, 1)),
        event_log=events, scenario=scenario, core_llm=FakeLLM(judge_queue),
        harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    return interactor, night, events


def test_submit_ratchets_identity_downgrade_and_recomputes_wrong():
    # 실판 재현 — 동일 문장 유지인데 LLM이 confirmed→none으로 흔들린 케이스
    prev = [{"id": "identity-1", "verdict": "confirmed",
             "matched_user_claim": "이송된 애들은 동물이야.", "cited": []}]
    interactor, night, events = _submit_env([{"verdict": "none", "matched_index": None}], prev)
    result = interactor.submit(night.id)

    item = night.per_truth_claim[0]
    assert item["verdict"] == "confirmed"
    assert item["ratcheted"] is True
    # 덩어리 칸이 문장 단위 후보로 갔는지 — 스키마 enum이 후보 2개
    schema = interactor._llm.calls[0][1]
    assert schema["properties"]["matched_index"]["anyOf"][0]["enum"] == [0, 1]
    # ratchet 매칭 문장은 wrong에서 빠진다
    assert result["wrong_claim_count"] == 1
    scored = next(e for e in events.recorded if e.__class__.__name__ == "AnswerScoredEvent")
    assert scored.per_truth_claim[0].ratcheted is True


def test_submit_shows_accepted_sentence_and_empty_cell_codes_but_not_truth():
    # 테스터10 F1 — 매 밤 인정된 내 문장과 빈 칸(원인·동기) 코드만. 진실 문장은 잠근다.
    truths = [SimpleNamespace(code="cause-1", cell="cause", text="채연이 아프다",
                              is_identity_word=False, world_outcomes=[])]
    interactor, night, _ = _submit_env(
        [{"verdict": "confirmed", "matched_index": 0}], [],
        ["채연이는 열이 있다. 트럭 소리가 났다."], truths)
    result = interactor.submit(night.id)

    assert result["accepted_claims"] == ["채연이는 열이 있다."]
    assert result["empty_cells"] == ["motive"]
    assert result["cell_feedback"] == "원인은 잡혔다."
    assert result["wrong_claim_count"] == 1
    assert result["truth_reveal"] is None
    assert "채연이 아프다" not in json.dumps(result, ensure_ascii=False)


def test_submit_shows_only_matched_one_of_near_duplicate_claims():
    # 리뷰 반영 — 정규화만 다른 두 후보 중 채점기가 0번만 지목 → 0번만 인정, 1번은 오답 수에 남는다
    truths = [SimpleNamespace(code="cause-1", cell="cause", text="채연이 아프다",
                              is_identity_word=False, world_outcomes=[])]
    interactor, night, _ = _submit_env(
        [{"verdict": "confirmed", "matched_index": 0}], [],
        ["트럭 소리가 났다", "트럭 소리가 났다."], truths)
    result = interactor.submit(night.id)

    assert result["accepted_claims"] == ["트럭 소리가 났다"]
    assert result["wrong_claim_count"] == 1


def test_submit_counts_ratcheted_identity_sentence_without_naming_identity():
    prev = [{"id": "identity-1", "verdict": "confirmed",
             "matched_user_claim": "이송된 애들은 동물이야.", "cited": []}]
    interactor, night, _ = _submit_env([{"verdict": "none", "matched_index": None}], prev)
    result = interactor.submit(night.id)

    assert result["accepted_claims"] == ["이송된 애들은 동물이야."]  # 칸 이름 없이
    assert result["empty_cells"] == ["cause", "motive"]
    assert result["cell_feedback"] is None  # "정체는 잡혔다"를 말하지 않는다
    assert "정체" not in json.dumps(result, ensure_ascii=False)
    assert "이들은 동물이다" not in json.dumps(result, ensure_ascii=False)


_FRAGMENT = "오후 검진을 시작합니다."


def test_fragment_matched_last_night_is_released_when_not_in_written_claims():
    # 테스터9 F11 재정정: 이어받은 기록 조각이 무관한 명제로 인정됐다. 조각은 플레이어가 쓴
    # 문장이 아니므로, 이번 글에 없으면 ratchet으로 붙잡지 않는다.
    prev = [{"id": "identity-1", "verdict": "confirmed", "matched_user_claim": _FRAGMENT, "cited": []}]
    claims, _ = draft_answer("채연은 검진을 피했다.", [_FRAGMENT])
    interactor, night, _ = _submit_env([{"verdict": "none", "matched_index": None}], prev, claims)
    interactor.submit(night.id)
    item = night.per_truth_claim[0]
    assert item["verdict"] == "none" and "ratcheted" not in item
    assert item["matched_user_claim"] is None


def test_fragment_copied_into_writing_keeps_ratchet():
    prev = [{"id": "identity-1", "verdict": "confirmed", "matched_user_claim": _FRAGMENT, "cited": []}]
    claims, _ = draft_answer(f"채연은 검진을 피했다. {_FRAGMENT}", [_FRAGMENT])
    interactor, night, _ = _submit_env([{"verdict": "none", "matched_index": None}], prev, claims)
    interactor.submit(night.id)
    item = night.per_truth_claim[0]
    assert item["verdict"] == "confirmed" and item["ratcheted"] is True
    assert item["matched_user_claim"] == _FRAGMENT


def test_chain_source_events_excludes_user_claims_and_meta():
    events = [
        ev.UtteranceEvent(
            loop_n=1, beat=1, target="채연", text="왜 남겼어?", reply="그냥.",
            budget_left=5, suspicion_delta=0, trust_delta=0, disclosure_level=0,
        ),
        ev.AnswerNormalizedEvent(
            loop_n=1, claims=["채연이 아프다"], user_edited=False, edit_diff=None,
        ),
        ev.AnswerWrongClaimsEvent(loop_n=1, claims=["민석이 감염됐다"]),
        ev.InterventionQuestionEvent(
            loop_n=1, q_index=1, question="누가?", answer="맞다",
            hit_cause_chain=True, confirmed_note_id=None,
        ),
        ev.RuleAppliedEvent(loop_n=1, rule_id="R1", source="user_choice", conflict=False),
    ]
    kept = chain_source_events(events)
    assert [e.type for e in kept] == [EventType.UTTERANCE, EventType.RULE_APPLIED]
