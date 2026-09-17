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
from apps.engine.adapter.outbound.repositories.scene_transaction import AttemptTransaction, SceneTransaction
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
        attempt_transaction=AttemptTransaction(db_session),
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
    res = inter.utter(info["loop_id"], npc.code, "여기 무슨 일이야?")
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
        inter.utter(info["loop_id"], npc.code, "왜 그래?")
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

    queue = [_agent_reply("응"), _agent_reply("응, 나도.")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    chars = [c for c in scenario.bundle().characters if c.playable]
    inter.utter(info["loop_id"], chars[0].code, "말")
    with pytest.raises(GameStateError, match="이 장면에서는 이미 대화했다"):
        inter.utter(info["loop_id"], chars[0].code, "또 말")
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == 7
    assert len(inter._npc_llm.calls) == 1

    # 한 인물의 대화 완료가 다른 인물까지 잠그지는 않는다.
    res = inter.utter(info["loop_id"], chars[1].code, "너는 어때?")
    assert res["reply"] == "응, 나도."
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


def test_agent_messages_can_omit_knowledge_block():
    from apps.engine.app.use_cases.game_support import build_agent_messages
    scenario = build_a()
    char = next(c for c in scenario.bundle().characters if c.code == "chaeyeon")
    with_k = build_agent_messages(scenario.bundle(), char, suspicion=0, trust=0, opposite=False,
                                  rules_text="", memory=[], user_text="안녕", loop_n=1, age7_on=True)
    without = build_agent_messages(scenario.bundle(), char, suspicion=0, trust=0, opposite=False,
                                   rules_text="", memory=[], user_text="안녕", loop_n=1, age7_on=True,
                                   include_knowledge=False)
    assert "[하루 시작 전부터 아는 것]" in with_k[0].content
    assert "[하루 시작 전부터 아는 것]" not in without[0].content
    assert "이송될 거라고 믿는다" not in without[0].content


def _harness_events(db_session, attempt):
    return [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "harness_event"]


def test_nonsense_is_gated_without_model_call_and_first_is_free(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    # 비트1 개시 시 시나리오A의 지나가는 말(ambient) 하네스와 무관 — 기준선을 잡는다
    before = len(_harness_events(db_session, attempt))
    res = inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    assert res["gated"] is True
    assert res["reply"] in npc.fallback_lines
    assert res["budget_left"] == 8
    assert res["npc"]["uttered"] is False
    assert len(_harness_events(db_session, attempt)) == before


def test_second_nonsense_in_same_beat_is_charged(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    res = inter.utter(info["loop_id"], npc.code, "......")
    assert res["budget_left"] == 7
    # 지나가는 말(ambient) 발화는 플레이어 입력이 아니므로 제외
    events = [e for e in EventLogRepository(db_session).query(attempt.id)
              if e.type == "utterance" and e.text != "(지나가는 말)"]
    assert [e.budget_charged for e in events] == [False, True]


def test_classifier_nonsense_is_gated_and_chat_omits_knowledge(db_session):
    # 큐: 분류기 nonsense → 즉답 / 분류기 chat + NPC 답 → 모델 호출은 지식 없이
    inter, scenario, attempt, info = make_day(db_session, [_agent_reply("응, 안녕.")])
    inter._core_llm = FakeLLM([{"label": "nonsense"}, {"label": "chat"}])
    npc = _first_npc(scenario)
    first = inter.utter(info["loop_id"], npc.code, "뭐라는거야ㅋ")
    assert first["gated"] is True and first["budget_left"] == 8
    second = inter.utter(info["loop_id"], npc.code, "안녕 좋은 아침")
    assert second["reply"] == "응, 안녕."
    agent_calls = [e for e in _harness_events(db_session, attempt) if e.role == "agent"]
    assert agent_calls and "[하루 시작 전부터 아는 것]" not in agent_calls[-1].call_records[0]["messages"][0]["content"]


def test_classifier_fallback_keeps_current_path(db_session):
    inter, scenario, attempt, info = make_day(db_session, [_agent_reply("배 안 고파.")])
    inter._core_llm = FakeLLM([])
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "왜 안어")
    assert res["reply"] == "배 안 고파."
    events = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "utterance"]
    assert events[-1].classification is None and events[-1].gated is False


def test_nonsense_utterance_after_day_ended_raises(db_session):
    """CRITICAL — 낮이 아니면 규칙 게이트(무의미 판정)보다 먼저 상태를 검사한다."""
    from apps.engine.app.use_cases.loop_interactor import GameStateError

    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.state = "night_pending"
    db_session.flush()
    with pytest.raises(GameStateError, match="낮이 아니면"):
        inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")


def test_budget_exhausted_normal_input_raises_before_classifier_call(db_session):
    """예산이 없으면 분류기(Core) 호출 전에 거부한다 — 거부될 발화에 모델 호출을 쓰지 않는다."""
    from apps.engine.app.use_cases.loop_interactor import GameStateError

    inter, scenario, attempt, info = make_day(db_session, [])
    inter._core_llm = FakeLLM([{"label": "chat"}])  # 분류기가 불려도 소비될 응답 — 호출되면 안 된다
    npc = _first_npc(scenario)
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.budget_left = 0
    db_session.flush()
    before = _harness_events(db_session, attempt)
    with pytest.raises(GameStateError):
        inter.utter(info["loop_id"], npc.code, "왜 그런지 설명해 줄래?")
    after = _harness_events(db_session, attempt)
    assert len(after) == len(before)
    assert not any(e.role == "classifier" for e in after)


def test_gated_input_beat_reset_is_free_again(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    first = inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    assert first["gated"] is True and first["budget_left"] == 8
    inter.advance_beat(info["loop_id"])
    second = inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    assert second["gated"] is True and second["budget_left"] == 8  # 새 비트 — 다시 무료


def test_gated_input_does_not_change_npc_state(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    before = LoopRepository(db_session).npc_state(info["loop_id"], npc.code)
    snapshot_before = (before.suspicion, before.trust, list(before.memory or []), before.uttered_beat)
    inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    after = LoopRepository(db_session).npc_state(info["loop_id"], npc.code)
    snapshot_after = (after.suspicion, after.trust, list(after.memory or []), after.uttered_beat)
    assert snapshot_after == snapshot_before


def test_manager_check_excludes_gated_utterances_from_user_utterances(db_session):
    """MINOR — 관리자 프롬프트 입력에서 게이트된(무의미) 발화는 제외한다."""
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    nonsense_text = "ㅋㅋㅋㅋ"
    inter.utter(info["loop_id"], npc.code, nonsense_text)
    inter.advance_beat(info["loop_id"])  # 비트 2 — MANAGER_CHECK_BEATS에서 관리자 점검이 돈다
    manager_calls = [e for e in _harness_events(db_session, attempt) if e.role == "manager_check"]
    assert manager_calls
    assert nonsense_text not in manager_calls[-1].call_records[0]["messages"][0]["content"]


def test_classifier_question_and_request_labels_take_normal_path_with_knowledge(db_session):
    inter, scenario, attempt, info = make_day(
        db_session, [_agent_reply("응, 그건 이래."), _agent_reply("알겠어.")]
    )
    inter._core_llm = FakeLLM([{"label": "question"}, {"label": "request"}])
    npc = _first_npc(scenario)
    inter.utter(info["loop_id"], npc.code, "그거 어떻게 된 거야?")
    inter.advance_beat(info["loop_id"])
    inter.utter(info["loop_id"], npc.code, "그거 좀 도와줄래?")
    agent_calls = [e for e in _harness_events(db_session, attempt) if e.role == "agent"]
    assert len(agent_calls) == 2
    for call in agent_calls:
        assert "[하루 시작 전부터 아는 것]" in call.call_records[0]["messages"][0]["content"]




def test_harness_regenerates_reply_with_invented_number(db_session):
    """테스터9 F14 — 기억·질문에 없는 숫자 값을 지어낸 답은 거부·재생성한다."""
    queue = [_agent_reply("내 거는 7이야. 다른 애는 5야."), _agent_reply("숫자는 잘 모르겠어.")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "손목띠 숫자 읽어 줄래?")
    assert res["reply"] == "숫자는 잘 모르겠어."


def test_harness_regenerates_reply_denying_remembered_own_trip(db_session):
    """테스터9 F14 — 기억에 간 곳을 안 갔다고 부정한 답은 거부·재생성한다."""
    queue = [_agent_reply("나는 오늘 방송실에 가지 않았어."), _agent_reply("방송실 문 앞까지 갔다 왔어.")]
    inter, scenario, attempt, info = make_day(db_session, queue)
    npc = _first_npc(scenario)
    repo = LoopRepository(db_session)
    state = repo.npc_state(info["loop_id"], npc.code)
    state.memory = [{"id": "went", "beat": 1, "kind": "내가 한 일", "text": "오늘 방송실에 갔어.",
                     "speaker": npc.name, "listeners": [npc.name], "source_ids": [], "forgotten": False}]
    repo.save()
    res = inter.utter(info["loop_id"], npc.code, "오늘 방송실에 가서 뭐 알렸어?")
    assert res["reply"] == "방송실 문 앞까지 갔다 왔어."
