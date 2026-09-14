"""Preview, persist and activate a rule on the player's question, never on scene entry."""
from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm, NightOrm
from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository, NightRepository, LoopRepository
from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.dependencies.engine_dependency import get_intervention_interactor
from apps.engine.domain.entities.question_rules import REPORT_QUESTION_ACTION
from tests.engine.test_usecase_day import make_day, _agent_reply


def add_question_rule(db_session, attempt):
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id='R1', source='user_custom',
        target='민석', when_beat=None, effect='enforce', action=REPORT_QUESTION_ACTION, created_loop=0))


def test_confirmed_preview_preserves_topic_and_question_trigger_in_stored_rule(db_session):
    day, _, attempt, info = make_day(db_session, [])
    loop = LoopRepository(db_session).get(info['loop_id'])
    loop.state = 'intervention'
    night = NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    inter = get_intervention_interactor(db_session)
    original = '민석이 보고하는 것을 내가 물어보면 상세하게 설명한다.'
    preview = inter.preview_rule(night.id, original)
    assert preview['executable'] and preview['alternatives'] == []
    result = inter.choose_rule(night.id, 'custom', original, preview['preview_id'])
    assert result['ok']
    saved = RuleRepository(db_session).list(attempt.id)[0]
    assert saved.action == REPORT_QUESTION_ACTION and saved.when_beat is None
    assert '내가 보고에 관해 물으면' in saved.shown_reason


def test_report_rule_enters_only_matching_question_and_records_actual_reply(db_session):
    day, _, attempt, info = make_day(db_session, [])
    add_question_rule(db_session, attempt)
    day.advance_beat(info['loop_id'])
    day.advance_beat(info['loop_id'])
    assert not [e for e in day._events.query(attempt.id) if e.type == 'rule_execution' and e.rule_id == 'R1']
    answer = '배급이 두 개 부족해서 보고했어.'  # Provider invention must never replace an authored rule response.
    day._npc_llm = FakeLLM([_agent_reply(answer)])
    response = day.utter(info['loop_id'], 'minseok', '방송실에 뭘 보고하는 거야?')
    assert day._npc_llm.calls == []
    assert response['reply'] != answer
    assert '채연' in response['reply'] and '적' in response['reply']
    records = [e for e in day._events.query(attempt.id) if e.type == 'rule_execution' and e.rule_id == 'R1']
    assert len(records) == 1 and records[0].observation_ids == [response['observations'][0]['observation_id']]
    assert records[0].actual_action == response['reply'] and records[0].result == 'obeyed'


def test_other_topic_does_not_trigger_report_rule(db_session):
    day, _, attempt, info = make_day(db_session, [_agent_reply('그냥 졸려.')])
    add_question_rule(db_session, attempt)
    day.utter(info['loop_id'], 'minseok', '오늘 잠은 잘 잤어?')
    prompt = day._npc_llm.calls[0][0][0].content
    assert REPORT_QUESTION_ACTION not in prompt
    assert not [e for e in day._events.query(attempt.id) if e.type == 'rule_execution' and e.rule_id == 'R1']


def test_question_rule_is_not_inserted_into_autonomous_daily_plan(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    add_question_rule(db_session, attempt)
    loop = LoopRepository(db_session).get(info['loop_id'])
    day._run_planner(loop, scenario.bundle())
    assert REPORT_QUESTION_ACTION not in day._core_llm.calls[-1][0][0].content
    npc = day._loops.npc_state(loop.id, 'minseok')
    assert not any(item['action'] == REPORT_QUESTION_ACTION for item in (npc.plan or []))


def test_report_rule_after_room_visit_reveals_own_report_without_invented_quantities(db_session):
    day, _, attempt, info = make_day(db_session, [])
    add_question_rule(db_session, attempt)
    for _ in range(4):
        day.advance_beat(info['loop_id'])
    result = day.utter(info['loop_id'], 'minseok', '방송실에 누구 얘기를 보고했어?')
    assert '채연' in result['reply'] and '알렸어' in result['reply']
    assert not day._npc_llm.calls


def test_changed_food_action_does_not_produce_original_accusation_in_rule_reply(db_session):
    day, _, attempt, info = make_day(db_session, [])
    add_question_rule(db_session, attempt)
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id='R2', source='user_custom',
        target='채연', when_beat=3, effect='suppress', action='배급을 남긴다', created_loop=0))
    for _ in range(4):
        day.advance_beat(info['loop_id'])
    result = day.utter(info['loop_id'], 'minseok', '누구를 보고했어?')
    assert '채연' not in result['reply']
    assert not day._npc_llm.calls
