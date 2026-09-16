"""진실 단계 공개(truth_reveal·엔딩 게이팅)와 회고 여정(journey_view) — 스포일러는 서버가 거른다."""

import uuid
from types import SimpleNamespace

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.use_cases.inspector_interactor import AccessDenied, InspectorInteractor
from apps.engine.app.use_cases.night_interactor import NightInteractor


class _RecorderEvents:
    def __init__(self):
        self.recorded = []

    def record(self, session_id, event):
        self.recorded.append(event)


_TRUTH = [
    SimpleNamespace(code="cause-1", cell="cause", text="채연이 감염의 시작이었다",
                    is_identity_word=False, world_outcomes=[]),
    SimpleNamespace(code="identity-1", cell="identity", text="이들은 동물이다",
                    is_identity_word=True, world_outcomes=[]),
]

_BY_CELL = {
    "identity": ["우리는 돼지였다."],
    "cause": ["감염의 시작은 채연이었다."],
    "motive": ["관리자는 농장주였다."],
}


def _final_submit_env(judge_queue, *, by_cell):
    loop = SimpleNamespace(
        id=uuid.uuid4(), attempt_id=uuid.uuid4(), loop_n=5, state="night_draft",
        rumor_index=0, score=None, anomaly_count=0, side_effect_claims=None,
        cause_chain=None, world_outcome=None,
    )
    night = SimpleNamespace(
        id=uuid.uuid4(), loop_id=loop.id, submitted=False,
        claims=["채연이 처음 아팠다.", "우리는 그냥 사람이야."],
        free_text="", tapped_note_ids=[], per_truth_claim=None,
        cell_scores=None, total=None, passed=None,
    )
    events = _RecorderEvents()
    events.query = lambda *a, **k: []
    scenario = SimpleNamespace(
        truth_claims=lambda: _TRUTH,
        bundle=lambda: SimpleNamespace(
            fragments=[], ending_lines=["전체 진실 덤프"],
            ending_outcomes={"truck": ["트럭이 왔다."]},
            ending_lines_by_cell=by_cell,
        ),
        beats=lambda: [SimpleNamespace(beat=6)],
    )
    attempt = SimpleNamespace(status="active", attempt_n=1, closed_by=None,
                              prior_cell_results=None)
    interactor = NightInteractor(
        attempts=SimpleNamespace(get=lambda _: attempt, save=lambda: None),
        loops=SimpleNamespace(get=lambda _: loop, save=lambda: None, npc_states=lambda _: []),
        notes=SimpleNamespace(upsert=lambda *a, **k: None), rules=None,
        nights=SimpleNamespace(get=lambda _: night, save=lambda: None,
                               previous_submitted=lambda a, n: None),
        event_log=events, scenario=scenario, core_llm=FakeLLM(judge_queue),
        harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    return interactor, night


# cause-1 → confirmed(후보 0), identity-1 → none
_JUDGE_QUEUE = [{"verdict": "confirmed", "matched_index": 0},
                {"verdict": "none", "matched_index": None}]


def test_final_truth_reveal_filters_unconfirmed():
    interactor, night = _final_submit_env(list(_JUDGE_QUEUE), by_cell=_BY_CELL)
    result = interactor.submit(night.id)
    reveal = {r["code"]: r for r in result["truth_reveal"]}
    assert reveal["cause-1"]["verdict"] == "confirmed"
    assert reveal["cause-1"]["truth"] == "채연이 감염의 시작이었다"
    assert reveal["cause-1"]["my_claim"] == "채연이 처음 아팠다."
    assert reveal["identity-1"]["verdict"] == "none"
    assert reveal["identity-1"]["truth"] is None  # 못 맞춘 진실은 서버가 내리지 않는다


def test_final_ending_lines_gate_by_cell_understanding():
    interactor, night = _final_submit_env(list(_JUDGE_QUEUE), by_cell=_BY_CELL)
    result = interactor.submit(night.id)
    lines = result["ending_lines"]
    assert "감염의 시작은 채연이었다." in lines      # cause 100 → 공개
    assert "우리는 돼지였다." not in lines            # identity 0 → 잠금
    assert "전체 진실 덤프" not in lines              # 일괄 덤프 경로는 쓰지 않는다
    assert "트럭이 왔다." in lines                    # outcome은 비스포일러 — 항상


def test_final_ending_lines_fallback_without_mapping():
    interactor, night = _final_submit_env(list(_JUDGE_QUEUE), by_cell={})
    result = interactor.submit(night.id)
    assert "전체 진실 덤프" in result["ending_lines"]  # 매핑 없는 시나리오는 기존 거동


# ── journey_view ─────────────────────────────────────────────────────

def _scored(loop_n, verdicts, total, passed):
    return ev.AnswerScoredEvent(
        loop_n=loop_n,
        per_truth_claim=[ev.TruthClaimVerdict(id=i, verdict=v, matched_user_claim=m,
                                              cited_chunks=[]) for i, v, m in verdicts],
        cell_scores=ev.CellScores(cause=c_cause, motive=0.0, side_effect=0.0,
                                  identity=c_identity),
        total=total, passed=passed,
    )


c_cause, c_identity = 100.0, 0.0


def _journey_env(events_list, notes):
    attempt_id = uuid.uuid4()
    attempt = SimpleNamespace(status="closed", closed_by="clear", attempt_n=1)
    scenario = SimpleNamespace(
        truth_claims=lambda: _TRUTH,
        bundle=lambda: SimpleNamespace(advisor_leads=[SimpleNamespace(
            key="truck", loop_n=1, cues=[], target="준", ask="트럭 소리를 들었는지",
            rule_action=None)]),
    )
    interactor = InspectorInteractor(
        attempts=SimpleNamespace(get=lambda _: attempt),
        rules=SimpleNamespace(list=lambda _: []),
        event_log=SimpleNamespace(query=lambda *a, **k: events_list),
        inspector_token="t", notes=SimpleNamespace(list=lambda _: notes),
        scenario=scenario,
    )
    return interactor, attempt_id


def test_journey_marks_newly_confirmed_once_and_collects_unlocked_notes():
    events_list = [
        _scored(1, [("cause-1", "none", None), ("identity-1", "none", None)], 13.1, False),
        _scored(2, [("cause-1", "confirmed", "채연이 처음 아팠다."),
                    ("identity-1", "none", None)], 40.0, False),
        _scored(3, [("cause-1", "confirmed", "채연이 처음 아팠다."),
                    ("identity-1", "none", None)], 42.0, False),
    ]
    notes = [SimpleNamespace(loop_n=2, source_key="advisor-lead-truck",
                             text="트럭은 실어 갈 뿐이다."),
             SimpleNamespace(loop_n=1, source_key="obs-1", text="일반 노트")]
    interactor, attempt_id = _journey_env(events_list, notes)
    journey = interactor.journey_view(attempt_id)

    l1, l2, l3 = journey["loops"]
    assert l1["new_confirmed"] == []
    assert [c["code"] for c in l2["new_confirmed"]] == ["cause-1"]
    assert l3["new_confirmed"] == []               # 이미 알아낸 건 다시 세지 않는다
    assert l2["unlocked_notes"] == ["트럭은 실어 갈 뿐이다."]
    assert l1["unlocked_notes"] == []              # 일반 노트는 해금 단서가 아니다


def test_journey_final_reveals_confirmed_only_and_hints_unresolved():
    events_list = [_scored(5, [("cause-1", "confirmed", "채연이 처음 아팠다."),
                               ("identity-1", "none", None)], 59.6, True)]
    interactor, attempt_id = _journey_env(events_list, [])
    journey = interactor.journey_view(attempt_id)

    reveal = {r["code"]: r for r in journey["final"]["truth_reveal"]}
    assert reveal["cause-1"]["truth"] == "채연이 감염의 시작이었다"
    assert reveal["identity-1"]["truth"] is None
    cells = {u["cell"] for u in journey["unresolved"]}
    assert "identity" in cells and "cause" not in cells
    assert all(u["hint"] for u in journey["unresolved"])  # 힌트는 리드 direction 재사용


def test_journey_requires_existing_attempt():
    interactor, _ = _journey_env([], [])
    interactor._attempts = SimpleNamespace(get=lambda _: None)
    with pytest.raises(AccessDenied):
        interactor.journey_view(uuid.uuid4())
