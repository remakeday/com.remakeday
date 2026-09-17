"""Player prose survives nights; conversational replies use bounded public context."""
from types import SimpleNamespace as NS
from uuid import uuid4

from apps.engine.app.use_cases.advisor_advice import WHY_PREFIX
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor, advisor_context
from apps.engine.app.use_cases.public_observations import disclose
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at
from tests.pure.test_question_stage_isolation import Stages


def test_previous_night_restores_exact_writing_not_selected_or_edited_claims():
    loop = loop_at()
    raw = "  채연은 아픈 것 같다.\n\n왜 숨길까?  "
    previous = NS(free_text=raw, claims=["검토 화면에서 바꾼 말", "선택한 기록"], tapped_note_ids=[7])
    inter = NightInteractor.__new__(NightInteractor)
    inter._loops = NS(get=lambda _: loop)
    inter._nights = NS(previous_submitted=lambda attempt, n: (previous, n - 1))
    assert inter.previous_answer(loop.id)["previous_answer"]["draft_text"] == raw


def test_inherited_selected_note_is_reference_only_and_stays_out_of_saved_writing():
    loop = loop_at()
    loop.state = "night_pending"
    saved = []
    inter = NightInteractor(attempts=None, loops=NS(get=lambda _: loop, save=lambda: None),
        notes=None, rules=None,
        nights=NS(for_loop=lambda _: None, create=saved.append), event_log=Events(),
        scenario=None, core_llm=None, harness_on=True, cookie_ab_on=False,
        night_cls=lambda **kw: NS(id=uuid4(), **kw))
    result = inter.draft(loop.id, [7], "내 추측.\n", [7])
    assert result["claims"] == ["내 추측."]
    assert saved[0].free_text == "내 추측.\n"


def advisor(records=0):
    loop, events = loop_at(), Events()
    loop.state = "intervention"
    bundle = build().bundle()
    for i in range(records):
        disclose(events, loop, bundle.beats[0], key=f"noise-{i}", text=f"준이 손목띠 {i}번을 본다.", actor="준")
    source = disclose(events, loop, bundle.beats[0], key="checkup",
        text="채연이 검진을 받았다. 결과는 공개되지 않았다.", actor="채연")
    # Even if the event store returns future observations, they must not reach the model.
    future = NS(**{**vars(loop), "loop_n": loop.loop_n + 1})
    disclose(events, future, bundle.beats[0], key="future", text="미래 전용 비밀 사건.", actor="채연")
    answer = "이곳에서는 상태가 안 좋은 사람을 다른 구역으로 이송해. 다만 채연의 검진 결과는 아직 공개되지 않았어."
    out = {"answer": answer, "question_kind": "lookup", "evidence": [
        {"id": source.observation_id, "quote": "결과는 공개되지 않았다.", "relation": "unknown"}]}
    model = Stages([out, {"answer": "이송을 걱정했을 가능성은 있지만, 숨긴 이유는 아직 확인되지 않았어.",
                          "question_kind": "lookup", "evidence": []}])
    night = NS(id=uuid4(), loop_id=loop.id, questions_left=3, questions=[])
    inter = InterventionInteractor(attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=None,
        nights=NS(get=lambda _: night, save=lambda: None), event_log=events, core_llm=model,
        action_vocab=[], target_names=["채연", "준"], harness_on=True, rule_cls=None,
        world_context=bundle.surface_summary)
    return inter, night, model, bundle, answer


def test_conditional_question_gets_natural_answer_in_one_call_with_only_public_context():
    inter, night, model, bundle, answer = advisor()
    result = inter.ask(night.id, "채연이 아프면 어떻게 돼?")
    assert result["answer"] == f"{WHY_PREFIX} {answer}"
    assert len(model.calls) == 1 and result["remaining"] == 3  # unknown 환급 (순서표 5번)
    context = model.calls[0][0][0].content
    assert bundle.surface_summary in context and "채연이 아프면 어떻게 돼?" in context
    assert bundle.hidden_truth not in context and "미래 전용 비밀 사건" not in context


def test_followup_receives_recent_question_and_answer():
    inter, night, model, _, answer = advisor()
    inter.ask(night.id, "채연이 아프면 어떻게 돼?")
    inter.ask(night.id, "그럼 왜 숨기는 걸까?")
    context = model.calls[1][0][0].content
    assert answer in context and "채연이 아프면 어떻게 돼?" in context
    assert "그럼 왜 숨기는 걸까?" in context


def test_large_record_collection_does_not_become_one_question_context_or_response():
    inter, night, model, _, _ = advisor(records=150)
    result = inter.ask(night.id, "채연이 아프면 어떻게 돼?")
    context = model.calls[0][0][0].content
    assert context.count("행위자:") <= 8
    assert "채연이 검진을 받았다. 결과는 공개되지 않았다." in context
    assert len(result["evidence"]) <= 2 and len(context) < 9000


def test_repeated_scene_keeps_distinct_loop_evidence_for_comparison():
    records = [NS(observation_id=f"loop-{n}", text="채연이 배급을 남겼다.", actor="채연",
                  verification="observed", loop_n=n, beat=1) for n in (1, 2)]
    selected = advisor_context("두 회차 모두 채연이 배급을 남겼어?", records, ["채연"])
    assert {o.loop_n for o in selected} == {1, 2}


def test_explicit_prior_loop_beats_recent_records_when_context_is_full():
    records = [NS(observation_id=f"loop-{n}:{beat}", text=f"채연이 배급을 {beat}숟갈 남겼다.",
                  actor="채연", verification="observed", loop_n=n, beat=beat)
               for n in range(1, 6) for beat in range(1, 7)]
    selected = advisor_context("1회차에 채연이 배급을 남겼어?", records, ["채연"])
    assert {o.beat for o in selected if o.loop_n == 1} == set(range(1, 7))
