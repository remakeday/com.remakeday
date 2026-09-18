"""question_suggestions 순수 함수 — 오늘 기록에서만, 가설 없는 찾기 질문, 같은 밤 질문 제외 (테스터9 F19 방향 3)."""

from types import SimpleNamespace as NS

import pytest

from apps.engine.app.use_cases.advisor_advice import guide_kind, is_wh_question, is_why_question
from apps.engine.app.use_cases.intervention_interactor import advisor_context, unresolved_question
from apps.engine.domain.entities.question_suggestions import (
    ACTOR_QUESTION,
    BROADCAST_QUESTION,
    NIGHT_CLUE_QUESTION,
    suggest_questions,
)

NAMES = ["채연", "민석", "준", "은상"]


def obs(key, *, loop_n=1, actor=None, verification="observed", text="…"):
    return NS(observation_id=f"loop-{loop_n}:{key}", loop_n=loop_n, actor=actor,
              verification=verification, text=text, beat=1)


def test_empty_observations_suggest_nothing():
    assert suggest_questions([], loop_n=1, asked=[]) == []


def test_only_records_of_the_current_loop_count():
    yesterday = [obs("broadcast-1", loop_n=1), obs("night-clue", loop_n=1),
                 obs("action-3-채연-남긴다", loop_n=1, actor="채연")]
    assert suggest_questions(yesterday, loop_n=2, asked=[]) == []


def test_order_is_broadcast_then_night_clue_then_most_recent_actor_and_limit_cuts():
    today = [obs("action-1-민석-적는다", actor="민석"), obs("broadcast-1"),
             obs("action-3-채연-남긴다", actor="채연"), obs("night-clue")]
    expected = [BROADCAST_QUESTION, NIGHT_CLUE_QUESTION, "채연은 오늘 무엇을 했는가?", "민석은 오늘 무엇을 했는가?"]
    assert suggest_questions(today, loop_n=1, asked=[], limit=4) == expected
    assert suggest_questions(today, loop_n=1, asked=[]) == expected[:3]


def test_at_most_two_actors_and_only_observed_actions_count():
    today = [obs("action-1-민석-적는다", actor="민석"), obs("action-2-준-본다", actor="준"),
             obs("action-3-채연-남긴다", actor="채연"),
             obs("ambient-4-0", actor="은상", verification="reported")]  # 흘린 말은 행동이 아니다
    assert suggest_questions(today, loop_n=1, asked=[], limit=5) == \
        ["채연은 오늘 무엇을 했는가?", "준은 오늘 무엇을 했는가?"]


@pytest.mark.parametrize("key", ["night-broadcast", "broadcast-3"])
def test_night_and_day_broadcasts_both_open_the_broadcast_question(key):
    assert suggest_questions([obs(key, verification="reported")], loop_n=1, asked=[]) == [BROADCAST_QUESTION]


def test_truck_fragment_alone_opens_the_night_clue_question():
    assert suggest_questions([obs("outcome-fragment-0")], loop_n=1, asked=[]) == [NIGHT_CLUE_QUESTION]


def test_questions_already_asked_tonight_are_dropped_ignoring_spacing_and_punctuation():
    today = [obs("broadcast-1"), obs("night-clue"), obs("action-3-채연-남긴다", actor="채연")]
    asked = ["오늘  방송에서 관리자는 무엇을 말했는가", "채연은 오늘 무엇을 했는가?!"]
    assert suggest_questions(today, loop_n=1, asked=asked) == [NIGHT_CLUE_QUESTION]


def test_topic_particle_follows_the_final_consonant():
    today = [obs("action-1-나리-본다", actor="나리"), obs("action-2-준-본다", actor="준")]
    assert suggest_questions(today, loop_n=1, asked=[]) == ["준은 오늘 무엇을 했는가?", "나리는 오늘 무엇을 했는가?"]


# ── 조언자가 이 문장들을 기록 찾기로 다루는지 — 안내 표에 먹히지 않고, 예/아니오 판정도 아니다 ──
_TEMPLATES = [BROADCAST_QUESTION, NIGHT_CLUE_QUESTION, ACTOR_QUESTION.format(name="채연은")]


@pytest.mark.parametrize("question", _TEMPLATES)
def test_templates_are_lookup_questions_not_guide_or_why(question):
    assert guide_kind(question, NAMES) is None
    assert is_wh_question(question) and not is_why_question(question)


@pytest.mark.parametrize("question", _TEMPLATES)
def test_templates_do_not_hold_the_verdict_back_on_a_plain_record(question):
    record = obs("broadcast-1", text="오후 검진을 시작합니다.", verification="reported")
    assert unresolved_question(question, [record]) is False


def test_today_question_ranks_current_loop_records_before_older_broadcasts():
    older = [NS(observation_id=f"loop-{n}:broadcast-1", text="이상한 점은 방송실로 알립니다.", actor=None,
                verification="reported", loop_n=n, beat=1) for n in range(1, 5)] * 2
    tonight = NS(observation_id="loop-5:night-broadcast", text="정리 작업이 있겠습니다.", actor=None,
                 verification="reported", loop_n=5, beat=6)
    selected = advisor_context(BROADCAST_QUESTION, older + [tonight], NAMES, today=5)
    assert selected[0] is tonight
