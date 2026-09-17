"""이해도는 생존 조건이 아니며, 다섯 번째 밤까지 모두 진행한다."""

import uuid
from types import SimpleNamespace as NS

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.inspector_interactor import InspectorInteractor, AccessDenied
from apps.engine.domain.entities.scoring_rules import total_score


class Memory:
    def __init__(self, row=None, rows=()):
        self.row, self.rows, self.recorded = row, list(rows), []

    def get(self, _id):
        return self.row

    def list(self, _id):
        return self.rows

    def save(self):
        pass

    def npc_states(self, _id):
        return []

    def previous_submitted(self, _attempt_id, _loop_n):
        return None

    def record(self, _id, event):
        self.recorded.append(event)

    def query(self, _id, *, loop_n=None):
        return [e for e in self.recorded if loop_n is None or getattr(e, 'loop_n', None) == loop_n]


def submit_night(loop_n, verdict, *, with_rule=False):
    attempt = NS(id=uuid.uuid4(), status='active', closed_by=None, attempt_n=1, cookies_seen=[])
    loop = NS(id=uuid.uuid4(), attempt_id=attempt.id, loop_n=loop_n, beat=6,
              rumor_index=0, state='night_draft', cause_chain=[], world_outcome=None)
    night = NS(id=uuid.uuid4(), loop_id=loop.id, claims=['상황과 정체에 대한 답'], submitted=False)
    events = Memory()
    truth = [NS(code=c, cell=c, text=c, is_identity_word=c == 'identity', world_outcomes=[])
             for c in ('cause', 'motive', 'identity')]
    rule = NS(rule_id='R1', source='monkey_paw', target='A', action='행동',
              effect='suppress', when_beat=1, created_loop=1)
    responses = []  # Side effects now come from actual execution events, never generated claims.
    responses += [{'verdict': verdict, 'matched_index': 0 if verdict == 'confirmed' else None, 'why': ''}] * 3
    responses += [{'chain': [{'beat': 1, 'fact': '세계에서 일어난 사건'}]}]
    interactor = NightInteractor(
        attempts=Memory(attempt), loops=Memory(loop), notes=None,
        rules=Memory(rows=[rule] if with_rule else []), nights=Memory(night),
        event_log=events, scenario=NS(truth_claims=lambda: truth, beats=lambda: [],
                                    bundle=lambda: NS(ending_lines=['숨겨진 상황의 결말'], ending_outcomes={}, fragments=[])),
        core_llm=FakeLLM(responses), harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    return interactor.submit(night.id), attempt, loop, events


@pytest.mark.parametrize('side', [0, 100])
def test_situation_is_seventy_and_side_effect_never_changes_total(side):
    assert total_score({'cause': 100, 'motive': 100, 'identity': 0, 'side_effect': side},
                       include_side_effect=True) == 70


@pytest.mark.parametrize('loop_n', [1, 2, 3, 4])
def test_perfect_understanding_still_goes_to_intervention(loop_n):
    result, attempt, loop, events = submit_night(loop_n, 'confirmed')
    assert result['total'] == 100
    assert not result['is_final'] and result['intervention_available']
    assert attempt.status == 'active' and loop.state == 'intervention'
    assert result['cells'] is None and result['cookie'] is None
    assert result['ending_lines'] is None
    assert result['world_outcome'] == loop.world_outcome == 'truck'
    assert not next(e for e in events.recorded if e.type == 'loop_end').survived


@pytest.mark.parametrize('verdict', ['none', 'confirmed'])
def test_fifth_night_closes_with_world_outcome_at_every_score(verdict):
    result, attempt, loop, events = submit_night(5, verdict)
    assert result['is_final'] and not result['intervention_available']
    assert attempt.status == loop.state == 'closed'
    assert result['world_outcome'] == loop.world_outcome == 'truck'
    assert result['cells'] is not None
    assert result['ending_lines'] == ['숨겨진 상황의 결말']
    assert len([e for e in events.recorded if e.type == 'session_end']) == 1
    assert InspectorInteractor(attempts=Memory(attempt), rules=Memory(), event_log=events,
                               inspector_token='secret').harness_view(attempt.id)


def test_paw_side_effect_is_not_an_answer_requirement():
    result, _, _, events = submit_night(2, 'confirmed', with_rule=True)
    scored = next(e for e in events.recorded if e.type == 'answer_scored')
    assert result['total'] == 100
    assert scored.cell_scores.side_effect == 0
    assert [v.id for v in scored.per_truth_claim] == ['cause', 'motive', 'identity']
    assert '부작용' not in (result['cell_feedback'] or '')


def test_retrospective_stays_locked_even_if_legacy_attempt_closed_early():
    attempt = NS(id=uuid.uuid4(), status='closed', closed_by='understood_all')
    inspector = InspectorInteractor(attempts=Memory(attempt), rules=Memory(), event_log=Memory(),
                                    inspector_token='secret')
    with pytest.raises(AccessDenied):
        inspector.harness_view(attempt.id)


def test_retrospective_counts_registered_rules_not_rejected_custom_attempts():
    _, attempt, _, events = submit_night(5, 'none')
    def rule(rid, source, conflict=False):
        return NS(rule_id=rid, source=source, target='A', when_beat=2, effect='suppress',
                  action='행동', shown_reason='표시한 이유', hidden_side_effect='설계된 대가',
                  created_loop=1, conflict=conflict)
    rules = [rule('R1', 'monkey_paw'), rule('R2', 'user_choice'), rule('R3', 'user_custom', True)]
    events.recorded += [
        ev.InterventionOptionsEvent(loop_n=2, options=['A', 'B', 'C'], chosen='custom', custom_text='거부된 제안'),
        ev.ToolCallEvent(loop_n=2, beat=3, caller='A', tool='ask_npc', args={},
                         result='응답', side_effect='의심 증가'),
        ev.HarnessEvent(loop_n=2, beat=3, role='agent', violations=['검사 거부'], attempts=3, fallback_used=True),
    ]
    data = InspectorInteractor(attempts=Memory(attempt), rules=Memory(rows=rules), event_log=events,
                               inspector_token='secret').harness_view(attempt.id)
    summary = data['harness_summary']
    assert summary['paw_accepted'] == 1
    assert summary['recommended_rules'] == summary['custom_rules'] == 1
    assert summary['rule_conflicts'] == 1
    assert summary['tool_side_effects'] == [{'loop_n': 2, 'beat': 3, 'text': '의심 증가'}]
    assert summary['rule_success_rate'] is None
    assert summary['fallbacks'] == 1


def test_retrospective_question_count_excludes_guide_answers():
    """안내 답(게임 목적·사용법)은 판정 질문이 아니다 — 회고의 질문 수에 넣지 않는다."""
    _, attempt, _, events = submit_night(5, 'none')
    def question(kind):
        return ev.InterventionQuestionEvent(loop_n=1, q_index=0 if kind == 'guide' else 1, question='질문',
                                            answer='답', hit_cause_chain=False, confirmed_note_id=None, kind=kind)
    events.recorded += [question('answer'), question('guide'), question('answer')]
    summary = InspectorInteractor(attempts=Memory(attempt), rules=Memory(), event_log=events,
                                  inspector_token='secret').harness_view(attempt.id)['harness_summary']
    assert summary['questions_asked'] == 2
