"""R3 결함 2 — 규칙의 결정적 강제: 계획 기계 보정·내레이션 보정 줄·프롬프트 규칙 최상단."""

import uuid

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.orms.game_state_orm import (
    LoopOrm,
    NpcStateOrm,
    RuleOrm,
)
from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.app.use_cases.game_support import build_agent_messages
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.manager_interactor import ManagerInteractor
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.domain.entities.rule_rules import (
    Rule,
    enforce_rules_on_plan,
    narration_with_rule_note,
)
from apps.scenarios.scenario_a.adapter import build as build_a


def _rule(target, action, effect, when_beat=None, rule_id="R1"):
    return Rule(
        rule_id=rule_id, source="user_choice", target=target,
        when_beat=when_beat, effect=effect, action=action, created_loop=1,
    )


# ── ① enforce_rules_on_plan 순수 함수 ──


def test_suppress_replaces_matching_action_with_neutral():
    plan = [
        {"beat": 1, "action": "배급을 남긴다", "note": ""},
        {"beat": 2, "action": "말을 건다", "note": ""},
    ]
    fixed = enforce_rules_on_plan(
        plan, [_rule("채연", "배급을 남긴다", "suppress")], neutral_action="혼자 있는다"
    )
    assert fixed[0]["action"] == "혼자 있는다"
    assert fixed[1]["action"] == "말을 건다"
    assert plan[0]["action"] == "배급을 남긴다"  # 원본 불변 (순수 함수)


def test_enforce_inserts_action_at_beat3_when_missing():
    plan = [{"beat": 1, "action": "말을 건다", "note": ""}]
    fixed = enforce_rules_on_plan(
        plan, [_rule("민석", "방송실에 간다", "enforce")], neutral_action="혼자 있는다"
    )
    assert {"beat": 3, "action": "방송실에 간다", "note": ""} in fixed


def test_enforce_replaces_action_at_when_beat():
    plan = [{"beat": 2, "action": "말을 건다", "note": ""}]
    fixed = enforce_rules_on_plan(
        plan, [_rule("민석", "방송실에 간다", "enforce", when_beat=2)],
        neutral_action="혼자 있는다",
    )
    assert fixed == [{"beat": 2, "action": "방송실에 간다", "note": ""}]


def test_no_rules_leaves_plan_unchanged():
    plan = [{"beat": 1, "action": "말을 건다", "note": ""}]
    assert enforce_rules_on_plan(plan, [], neutral_action="혼자 있는다") == plan


# ── ②③④ 통합 — core_llm 큐·규칙 선주입이 가능한 로컬 헬퍼 ──


def make_day_with_rules(db_session, npc_queue, core_queue, *, rules=()):
    """make_day 변형 — start_loop 전에 규칙을 심고 core_llm 큐(Planner)를 공급한다."""
    scenario = build_a()
    core_llm = FakeLLM(core_queue)
    interactor = LoopInteractor(
        attempts=AttemptRepository(db_session),
        loops=LoopRepository(db_session),
        notes=NoteRepository(db_session),
        rules=RuleRepository(db_session),
        event_log=EventLogRepository(db_session),
        scenario=scenario,
        npc_llm=FakeLLM(npc_queue),
        core_llm=core_llm,
        manager=ManagerInteractor(core_llm=core_llm, scenario=scenario, harness_on=True),
        harness_on=True, age7_on=True, paw_reason_ab_on=True,
        loop_cls=LoopOrm, npc_state_cls=NpcStateOrm, rule_cls=RuleOrm,
    )
    attempt = AttemptRepository(db_session).create(None)
    rule_repo = RuleRepository(db_session)
    for i, (target, action, effect, when_beat) in enumerate(rules):
        rule_repo.add(RuleOrm(
            attempt_id=attempt.id, rule_id=f"R{i + 1}", source="user_choice",
            target=target, when_beat=when_beat, effect=effect, action=action,
            created_loop=1,
        ))
    info = interactor.start_loop(attempt.id)
    return interactor, scenario, attempt, info


def _plan_of(db_session, loop_id, code):
    return LoopRepository(db_session).npc_state(uuid.UUID(loop_id), code).plan


def test_planner_plan_corrected_by_suppress_rule(db_session):
    planner_out = {"plans": [{"npc": "채연", "beats": [
        {"beat": 1, "action": "배급을 남긴다", "note": ""},
        {"beat": 2, "action": "혼자 있는다", "note": ""},
    ]}]}
    inter, scenario, attempt, info = make_day_with_rules(
        db_session, [], [planner_out],
        rules=[("채연", "배급을 남긴다", "suppress", None)],
    )
    plan = _plan_of(db_session, info["loop_id"], "chaeyeon")
    assert plan is not None
    assert all(b["action"] != "배급을 남긴다" for b in plan)
    assert plan[1]["action"] == "혼자 있는다"  # 규칙과 무관한 비트는 그대로


def test_planner_fallback_still_enforces_rule(db_session):
    inter, scenario, attempt, info = make_day_with_rules(
        db_session, [], [],  # Planner 폴백 (계획 없음)
        rules=[("민석", "방송실에 간다", "enforce", None)],
    )
    plan = _plan_of(db_session, info["loop_id"], "minseok")
    assert plan and any(b["action"] == "방송실에 간다" for b in plan)


# ── ③ 내레이션 보정 줄 ──


def test_narration_gets_rule_correction_line(db_session):
    inter, scenario, attempt, info = make_day_with_rules(
        db_session, [], [], rules=[("채연", "배급을 남긴다", "suppress", None)],
    )
    # 비트 1: "배급 줄이 생긴다 … 채연이 자기 몫을 반쯤 남기고" — target·어간 모두 등장
    assert "반쯤 남기고" not in info["narration"]
    assert "채연" in info["narration"]
    inter.advance_beat(info["loop_id"])  # → 비트 2: 조합 없음
    res3 = inter.advance_beat(info["loop_id"])  # → 비트 3: "정오 배급 … 채연이 쟁반을"
    assert "채연은 쟁반을 밀어내지 않는다" in res3["narration"]


def test_narration_unchanged_without_matching_rule(db_session):
    inter, scenario, attempt, info = make_day_with_rules(db_session, [], [])
    assert "채연이 자기 몫을 반쯤 남기고" in info["narration"]
    inter.advance_beat(info["loop_id"])
    res = inter.advance_beat(info["loop_id"])
    assert "민석이 배급 자리를 보고 수첩에" in res["narration"]


# ── ④ 프롬프트 순서 — 규칙이 페르소나보다 앞 ──


def test_agent_prompt_puts_rules_before_persona():
    bundle = build_a().bundle()
    char = next(c for c in bundle.characters if c.playable)
    sys = build_agent_messages(
        bundle, char,
        rules_text="[R1] 채연은(는) 하루 종일에 배급을 남긴다 — 반드시 하지 않는다",
        suspicion=0, trust=50, opposite=False, memory=[],
        user_text="안녕", loop_n=1, age7_on=True,
    )[0].content
    assert sys.index("[오늘의 규칙]") < sys.index("[너에 대해]")
    assert "오늘의 법" in sys


def test_authored_dialogue_uses_executed_scene_without_a_model_call(db_session):
    inter, scenario, attempt, info = make_day_with_rules(db_session, [], [])
    response = inter.advance_beat(info["loop_id"])
    assert response["ambient"]["lines"][0]["code"] == "jun"
    assert "이 숫자 뭔지 알아?" in response["ambient"]["lines"][0]["text"]
    assert inter._npc_llm.calls == []


# ── ⑤ R3 이슈 1: 보정 줄은 활성 규칙 전체에 적용 ──


def test_rule_note_appends_line_per_matching_rule():
    """한 내레이션에 규칙 둘이 매칭되면 보정 줄도 둘 — 첫 매칭에서 멈추지 않는다."""
    narration = "채연이 배급을 남긴다. 민석이 방송실 문 앞을 오간다."
    rules = [
        _rule("채연", "배급을 남긴다", "suppress", rule_id="R1"),
        _rule("민석", "방송실에 간다", "suppress", rule_id="R2"),
    ]
    out = narration_with_rule_note(narration, rules, 1)
    assert out.count("오늘은 다르다") == 2
    assert "채연은(는) 그러지 않는다" in out
    assert "민석은(는) 그러지 않는다" in out


def test_rule_note_merges_duplicate_lines_for_same_target():
    """같은 대상에 규칙 둘이 매칭돼도 중복 문구는 한 줄로 합친다."""
    narration = "정오 배급이 나온다. 채연이 쟁반을 밀어낸다."
    rules = [
        _rule("채연", "배급을 남긴다", "suppress", rule_id="R1"),
        _rule("채연", "쟁반을 민다", "suppress", rule_id="R2"),
    ]
    out = narration_with_rule_note(narration, rules, 3)
    assert out.count("오늘은 다르다") == 1


def test_two_rules_each_correct_their_own_beats(db_session):
    """서로 다른 회차에 등록된 규칙 각각이 자기 모순 내레이션을 보정한다."""
    inter, scenario, attempt, info = make_day_with_rules(
        db_session, [], [],
        rules=[
            ("채연", "배급을 남긴다", "suppress", None),
            ("민석", "방송실에 간다", "suppress", None),
        ],
    )
    assert "채연은 오늘 쟁반을 옆으로 밀지 않는다" in info["narration"]  # 비트 1
    for _ in range(3):
        inter.advance_beat(info["loop_id"])
    res5 = inter.advance_beat(info["loop_id"])  # 비트 5: "민석이 방송실 문 앞을 …"
    assert "민석은 방송실 문 쪽으로 가지 않았다" in res5["narration"]


# ── ⑥ R3 이슈 1: 신의 정본 — 원인 체인 입력에도 보정 반영 ──


def test_cause_chain_input_uses_rule_corrected_narration(db_session):
    """_make_cause_chain의 비트_서술은 보정 통과본 — 신이 읽는 기록도 규칙 이후 세계다."""
    attempt = AttemptRepository(db_session).create(None)
    RuleRepository(db_session).add(RuleOrm(
        attempt_id=attempt.id, rule_id="R1", source="user_choice",
        target="채연", when_beat=None, effect="suppress",
        action="배급을 남긴다", created_loop=1,
    ))
    loop = LoopOrm(attempt_id=attempt.id, loop_n=1, beat=6, budget_left=0, state="day")
    LoopRepository(db_session).create(loop, [])
    night = NightInteractor(
        attempts=AttemptRepository(db_session), loops=LoopRepository(db_session),
        notes=None, rules=RuleRepository(db_session), nights=None,
        event_log=EventLogRepository(db_session), scenario=build_a(),
        core_llm=FakeLLM([]), harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    night._make_cause_chain(loop)
    assert loop.cause_chain == []  # No publicly disclosed scenes in this seeded loop.
    assert night._llm.calls == []  # Registration is not a source of world facts.


# ── ⑦ R3 이슈 1 참고: 계획 보정이 잡담 프롬프트까지 흐르는 경로 ──


def test_authored_dialogue_is_unaffected_by_an_unrelated_suppressed_plan(db_session):
    planner_out = {"plans": [{"npc": "채연", "beats": [
        {"beat": 2, "action": "배급을 남긴다", "note": ""},
    ]}]}
    inter, scenario, attempt, info = make_day_with_rules(
        db_session, [], [planner_out],
        rules=[("채연", "배급을 남긴다", "suppress", None)],
    )
    response = inter.advance_beat(info["loop_id"])
    assert response["ambient"]["lines"][0]["text"] == "민석아, 이 숫자 뭔지 알아?"
    assert "채연" not in str(response["ambient"])
    assert inter._npc_llm.calls == []
