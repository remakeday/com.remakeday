"""Preserve subject and player-question condition instead of broadening a custom rule."""
from types import SimpleNamespace as NS
import pytest
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from tests.pure.test_review_failure_boundaries import loop_at
from apps.engine.domain.entities.question_rules import question_matches, REPORT_QUESTION_ACTION


def interactor():
    return InterventionInteractor(attempts=None, loops=None, notes=None, rules=None, nights=None,
        event_log=None, core_llm=None, action_vocab=['기록한다'], target_names=['민석', '채연'],
        harness_on=True, rule_cls=None, question_rule_targets=['민석'])


@pytest.mark.parametrize('text', [
    '민석이 보고하는 것을 내가 물어보면 상세하게 설명한다.',
    '민석은 내가 보고에 관해 물으면 자세히 설명한다.',
    '민석은 보고 내용을 질문하면 구체적으로 말한다.',
])
def test_report_question_rule_preserves_player_trigger_and_topic(text):
    rule, reason = interactor()._map_custom(loop_at(), text)
    assert rule is not None, reason
    assert rule['target'] == '민석' and rule['when_beat'] == 'any'
    assert '보고' in rule['action'] and '물으면' in rule['action']
    assert '내가' in rule['label'] and '자세히' in rule['label']


@pytest.mark.parametrize('text', [
    '민석은 보고 내용을 채연이 물으면 자세히 설명한다.',
    '민석은 보고 내용을 내가 물으면 거짓으로 자세히 설명한다.',
    '민석은 내일 오후에만 내가 보고에 관해 물으면 자세히 설명한다.',
    '민석은 보고를 하지 않았다면 내가 물으면 자세히 설명한다.',
    '민석은 보고 내용을 내가 물으면 설명하지 않는다.',
    '민석은 내가 보고한 내용을 물으면 자세히 설명한다.',
])
def test_extra_recipient_time_negation_or_truth_constraints_are_not_silently_dropped(text):
    rule, _ = interactor()._map_custom(loop_at(), text)
    assert rule is None


@pytest.mark.parametrize('text', [
    '채연이 왜 담요를 보고 있어?', '방송실이 어디야?',
    '오늘은 보고 얘기 말고 손목띠 얘기하자.', '네가 신고 있는 신발은 뭐야?',
    '오늘 보고할게.',
])
def test_unrelated_homonyms_location_exclusion_or_statement_does_not_activate(text):
    assert not question_matches(REPORT_QUESTION_ACTION, text)


@pytest.mark.parametrize('text', [
    '방송실에 뭘 보고하는 거야?', '누구를 신고했어?', '오늘 보고 안 했어?',
    '손목띠 말고 보고한 내용을 말해 줘.', '방송실에 무슨 말을 전했어?',
])
def test_actual_report_questions_and_requests_activate(text):
    assert question_matches(REPORT_QUESTION_ACTION, text)
