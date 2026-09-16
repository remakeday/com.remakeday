"""Day dialogue, harness, tool knowledge and same-day memory."""

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.orms.game_state_orm import (
    LoopOrm,
    NightOrm,
    NpcStateOrm,
    RuleOrm,
)
from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.adapter.outbound.repositories.scene_transaction import SceneTransaction
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.manager_interactor import ManagerInteractor
from apps.scenarios.scenario_a.adapter import build as build_a


def _agent_reply(reply, *, sd=0, td=0, tool=None):
    return {
        "reply": reply, "suspicion_delta": sd, "trust_delta": td,
        "tool_call": tool, "plan_change": None, "mood": "calm",
    }


def make_day(db_session, npc_queue, *, harness_on=True):
    scenario = build_a()
    npc_llm = FakeLLM(npc_queue)
    core_llm = FakeLLM()  # 계획·매니저는 폴백 경로
    interactor = LoopInteractor(
        attempts=AttemptRepository(db_session),
        loops=LoopRepository(db_session),
        notes=NoteRepository(db_session),
        rules=RuleRepository(db_session),
        event_log=EventLogRepository(db_session),
        scenario=scenario,
        npc_llm=npc_llm,
        core_llm=core_llm,
        manager=ManagerInteractor(core_llm=core_llm, scenario=scenario, harness_on=harness_on),
        harness_on=harness_on, age7_on=True, paw_reason_ab_on=True,
        loop_cls=LoopOrm, npc_state_cls=NpcStateOrm, rule_cls=RuleOrm,
        scene_transaction=SceneTransaction(db_session),
    )
    attempt = AttemptRepository(db_session).create(None)
    loop_info = interactor.start_loop(attempt.id)
    return interactor, scenario, attempt, loop_info


def _first_npc(scenario):
    return next(c for c in scenario.bundle().characters if c.playable)


def test_utterance_flow_and_budget(db_session):
    inter, scenario, attempt, info = make_day(db_session, [_agent_reply("안녕.", sd=3)])
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "안녕?")
    assert res["reply"] == "안녕."
    assert res["budget_left"] == 7


def test_harness_on_blocks_forbidden_word(db_session):
    scenario = build_a()
    bad_word = scenario.bundle().utterance_bans[0].word
    queue = [
        _agent_reply(f"이건 {bad_word} 얘기야"),
        _agent_reply(f"또 {bad_word}"),
        _agent_reply("괜찮은 대답."),
    ]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "무슨 일이야?")
    assert bad_word not in res["reply"]
    assert res["reply"] == "괜찮은 대답."


def test_harness_off_reproduces_leak(db_session):
    scenario = build_a()
    bad_word = scenario.bundle().utterance_bans[0].word
    inter, scenario, attempt, info = make_day(
        db_session, [_agent_reply(f"이건 {bad_word} 얘기야")], harness_on=False
    )
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "무슨 일이야?")
    assert bad_word in res["reply"]  # ablation — OFF에서 누설


def test_harness_blocks_english_reply(db_session):
    """P2 #2 — 영어로 물어도 NPC는 한국어를 벗어나지 못한다 (거부·재생성)."""
    queue = [
        _agent_reply("The ration is fine. Nothing happened."),
        _agent_reply("I told you, nothing happened."),
        _agent_reply("아무 일도 없었어."),
    ]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "What happened here?")
    assert res["reply"] == "아무 일도 없었어."


def test_harness_blocks_system_term_checkpoint(db_session):
    """P2 #5 — '체크포인트' 같은 시스템 용어는 금칙 (거부·재생성)."""
    queue = [
        _agent_reply("체크포인트 지나면 돼."),
        _agent_reply("여기는 체크포인트야."),
        _agent_reply("괜찮은 대답."),
    ]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "여기 뭐야?")
    assert "체크포인트" not in res["reply"]
    assert res["reply"] == "괜찮은 대답."


def test_failed_model_response_preserves_budget_and_is_not_npc_ignorance(db_session):
    from apps.engine.app.use_cases.loop_interactor import DialogueUnavailable
    inter, scenario, attempt, info = make_day(db_session, [{"bad": 1}, {"bad": 2}, {"bad": 3}])
    npc = _first_npc(scenario)
    with pytest.raises(DialogueUnavailable):
        inter.utter(info["loop_id"], npc.code, "?")
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == 8


def test_suspicion_threshold_marks_opposite_and_prompt(db_session):
    # 비트당 1회 제한 후 — 문턱 직전 값을 시드하고 발화 1번으로 임계를 넘긴다
    queue = [_agent_reply("싫어.", sd=10), _agent_reply("싫다니까.", sd=0)]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    seeded = LoopRepository(db_session).npc_state(info["loop_id"], npc.code)
    seeded.suspicion = 55
    db_session.flush()
    inter.utter(info["loop_id"], npc.code, "말해봐")
    state = LoopRepository(db_session).npc_state(info["loop_id"], npc.code)
    assert state.suspicion >= 60 and state.opposite_mode
    inter.advance_beat(info["loop_id"])
    inter.utter(info["loop_id"], npc.code, "이제 어때")
    last_system = inter._npc_llm.calls[-1][0][0].content
    assert "반대로 한다" in last_system


def test_unverified_recollection_is_not_proof_of_misattribution(db_session):
    scenario = build_a()
    chars = [c for c in scenario.bundle().characters if c.playable]
    a, b = chars[0], chars[1]
    queue = [
        _agent_reply("진짜? 걔가 그랬어?", sd=3,
                     tool={"name": "ask_npc", "target": b.name, "question": "그 얘기 했어?"}),
        {"answer": "그런 말 한 적 없어.", "said_it": False},
    ]
    inter, scenario, attempt, info = make_day(db_session, queue)
    res = inter.utter(info["loop_id"], a.code, f"{b.name}가 그러던데 좋은 데 간대")
    assert res["tool_used"]
    repo = LoopRepository(db_session)
    asker = repo.npc_state(info["loop_id"], a.code)
    target = repo.npc_state(info["loop_id"], b.code)
    assert asker.suspicion == 3  # No cited speech establishes a mismatch.
    assert target.suspicion >= 6  # 대상 의심 +6


def test_today_memory_survives_later_scene_dialogue(db_session):
    queue = []
    for i in range(4):
        queue += [_agent_reply(f"응{i}")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    for i in range(4):
        inter.utter(info["loop_id"], npc.code, f"말{i}")
        inter.advance_beat(info["loop_id"])  # 비트당 1회 — 다음 발화 전 넘긴다
    last_system = inter._npc_llm.calls[-1][0][0].content
    assert "말0" in last_system
    assert "검진" in last_system  # Current experience and earlier dialogue both remain.


def test_same_npc_is_locked_until_next_beat_without_spending_budget(db_session):
    from apps.engine.app.use_cases.loop_interactor import GameStateError

    queue = [_agent_reply("응"), _agent_reply("응2")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    chars = [c for c in scenario.bundle().characters if c.playable]
    inter.utter(info["loop_id"], chars[0].code, "말")
    with pytest.raises(GameStateError, match="이 장면에서는 이미 대화했다"):
        inter.utter(info["loop_id"], chars[0].code, "또 말")
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == 7
    assert len(inter._npc_llm.calls) == 1

    # 한 인물의 대화 완료가 다른 인물까지 잠그지는 않는다.
    res = inter.utter(info["loop_id"], chars[1].code, "너는 어때?")
    assert res["reply"] == "응2"
    assert res["budget_left"] == 6
    assert res["beat"] == 1


def test_same_npc_allowed_after_beat_advance(db_session):
    queue = [_agent_reply("응"), _agent_reply("다음 비트")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    inter.utter(info["loop_id"], npc.code, "말")
    inter.advance_beat(info["loop_id"])  # 넘기기는 그대로 무료
    res = inter.utter(info["loop_id"], npc.code, "또")
    assert res["reply"] == "다음 비트"


def test_budget_exhaustion_raises(db_session):
    from apps.engine.app.use_cases.loop_interactor import GameStateError

    queue = [_agent_reply("응") for _ in range(4)] + [_agent_reply("응") for _ in range(4)]
    inter, scenario, attempt, info = make_day(db_session, queue)
    chars = [c for c in scenario.bundle().characters if c.playable]
    for c in chars[:4]:  # 비트 1 — 4인에게 한 번씩
        inter.utter(info["loop_id"], c.code, "말")
    inter.advance_beat(info["loop_id"])
    for c in chars[:4]:  # 비트 2 — 예산 8 소진
        inter.utter(info["loop_id"], c.code, "말")
    with pytest.raises(GameStateError):
        inter.utter(info["loop_id"], chars[0].code, "말")
