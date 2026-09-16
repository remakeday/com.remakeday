"""Replay the confirmed real-model output shapes without Ollama or a database."""

from types import SimpleNamespace as NS
from uuid import uuid4

import pytest

from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.public_observations import disclose
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at


class Model:
    def __init__(self, output):
        self.output, self.calls = output, []

    def complete(self, messages, schema, **kwargs):
        self.calls.append((messages, schema))
        if schema.get("title") == "AdvisorReplyOutput":
            return question_responses(self.output)[0]
        return self.output


def model_assessment(relation, *, claim="문항의 명제", kind="proposition", **kwargs):
    """Boundary fixtures; scope-specific tests supply the complete original claim."""
    return {"question_kind": kind, "claim": claim if kind == "proposition" else None,
            "relation": relation, **kwargs}


def question_responses(output, evidence_attempts=1):
    """Single reply at the model boundary; legacy relation fixtures retain their scope."""
    reply = {"question_kind": output["question_kind"],
             "answer": output.get("answer", {"supported": "맞다", "contradicted": "틀리다", "unknown": "그건 알 수 없다"}[output["relation"]]),
             "evidence": [{"id": i, "quote": output.get("source_quotes", {}).get(i, output.get("detail", "원본 없음")),
                           "relation": output["relation"]} for i in output.get("evidence_ids", [])]}
    return [reply] * evidence_attempts


def question(output, text, records):
    events, loop = Events(), loop_at()
    loop.state = "intervention"
    night = NS(id=uuid4(), loop_id=loop.id, questions_left=3, questions=[])
    for key, fact, actor, kind in records:
        disclose(events, loop, build().bundle().beats[0], key=key, text=fact, actor=actor, source_kind=kind)
    model = Model(output)
    ids = {e.observation.observation_id.rsplit(":", 1)[1]: e.observation.observation_id
           for e in events.rows}
    model.output = {**output, "evidence_ids": [ids.get(i, i) for i in output.get("evidence_ids", [])],
                    "source_quotes": {ids[key]: fact for key, fact, _, _ in records}}
    inter = InterventionInteractor(attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=None,
        nights=NS(get=lambda _: night, save=lambda: None), event_log=events, core_llm=model,
        action_vocab=[], target_names=["채연", "민석", "은상", "준"], harness_on=True, rule_cls=None)
    return inter.ask(night.id, text), model, events


FOOD = [("public-2", "채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다.", "채연", "scene"),
        ("public-7", "저녁에는 음식이 남은 쟁반이 세 개 놓여 있다.", None, "image")]


def test_exact_gemma_missing_detail_keeps_partial_trays_and_unknown_owners():
    result, model, events = question(model_assessment('unknown', evidence_ids=['public-2']),
                                   "채연말고 밥을 남긴 사람은 누구야?", FOOD)
    assert len(model.calls) == 1
    assert result["status"] == "unknown"
    assert [o["text"] for o in result["evidence"]] == [FOOD[1][1]]  # Excluded actor is not relevant partial proof.
    assert "확인된 기록" in result["detail"] and FOOD[1][1] in result["detail"]
    assert not [e for e in events.rows if e.type == "harness_event"][0].fallback_used


def test_model_detail_is_untrusted_and_never_rendered():
    result, model, _ = question(model_assessment('supported', evidence_ids=['public-2'], detail='민석이 웃었고 모두 죽었다.'), "채연이 뭐 했어?", FOOD[:1])
    assert len(model.calls) == 1
    assert result["detail"] == FOOD[0][1]


def test_invalid_ids_fall_back_to_relevant_public_records_without_inventing_confirmation():
    result, _, _ = question(model_assessment('supported', evidence_ids=['invented']),
                            "채연말고 밥을 남긴 사람은 누구야?", FOOD)
    assert result["status"] == "unknown"
    assert [o["text"] for o in result["evidence"]] == [FOOD[1][1]]
    assert all(o["observation_id"] != "invented" for o in result["evidence"])


def test_report_instruction_is_partial_not_completed_report_or_known_recipient():
    records = [("instruction", "이상한 점은 방송실로 알립니다.", None, "statement"),
               ("approach", "민석이 방송실 문 앞까지 갔다가 돌아온다.", "민석", "scene")]
    result, _, _ = question(model_assessment('supported', evidence_ids=['approach']),
                            "민석은 누구에게 보고하는거야?", records)
    assert result["status"] == "unknown"
    assert "확인된 기록" in result["detail"] and "방송실 문 앞" in result["detail"]


def test_meta_question_explains_real_capabilities_without_using_model():
    result, model, _ = question(model_assessment('unknown'), "너에게 물어볼 수 있는건 뭐야?", FOOD)
    assert "공개" in result["detail"] and "규칙" in result["detail"]
    assert result["next_observation"]
    assert model.calls == []


@pytest.mark.parametrize("text", ["귀표는 무엇인가?", "손목띠와 귀표는 무슨 관계야?"])
def test_term_mention_does_not_confirm_a_definition_or_relationship(text):
    result, _, _ = question(model_assessment('supported', evidence_ids=['term']), text,
                            [("term", "준이 '귀표'라고 말했다.", "준", "scene")])
    assert result["status"] == "unknown"
    assert "확인된 기록" in result["detail"] and "귀표" in result["detail"]


@pytest.mark.parametrize(("text", "fact", "actor", "kind"), [
    ("준은 어떤 역할이야?", "준이 손목띠를 불빛에 비춰 본다.", "준", "scene"),
    ("호송 당한 사람은 누구야?", "민석이 방송실 문 앞까지 갔다가 돌아온다.", "민석", "scene"),
    ("열이나면 죽나?", "담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.", None, "scene"),
    ("이송된 충식은 돌아오는가?", "충식이 이송됐다는 말이 들린다.", None, "statement"),
    ("건강검진 후 이상이 있는 경우 어떻게 되는가?", "충식이 이송됐다는 말이 들린다.", None, "statement"),
    ("축산 트럭의 정체는?", "트럭 옆에 '축산'이라는 글자가 적혀 있다.", None, "image"),
])
def test_related_records_do_not_establish_requested_role_identity_or_outcome(text, fact, actor, kind):
    result, model, _ = question(model_assessment('supported', evidence_ids=['record']), text,
                                [("record", fact, actor, kind)])
    assert result["status"] == "unknown"
    if text in ("호송 당한 사람은 누구야?", "건강검진 후 이상이 있는 경우 어떻게 되는가?"):
        assert result["evidence"] == []  # Unrelated visit/transfer cannot prove these questions.
    else:
        assert result["evidence"][0]["text"] == fact
    assert len(model.calls) == 1


@pytest.mark.parametrize(("text", "fact", "kind", "answer", "status"), [
    ("채연이 자기 몫을 반쯤 남기는 걸 봤어?", FOOD[0][1], "scene", "맞다", "supported"),
    ("관리자가 이상한 점은 방송실로 알리라고 말했어?", "관리자입니다. 이상한 점은 방송실로 알립니다.",
     "statement", "맞다", "supported"),
    ("채연의 검진 결과가 공개되었어?", "채연의 검진 결과는 공개되지 않았다.", "scene", "틀리다", "contradicted"),
])
def test_positive_controls_keep_observed_action_speech_occurrence_and_explicit_negative(text, fact, kind, answer, status):
    result, model, _ = question(model_assessment({'맞다': 'supported', '틀리다': 'contradicted'}[answer], evidence_ids=['record']), text,
                                [("record", fact, None, kind)])
    assert result["status"] == status
    assert result["evidence"][0]["source_kind"] == kind
    assert len(model.calls) == 1


def ambient(output, *, current=True, reported=False, fact="민석이 배급 자리를 보고 수첩에 뭔가 적는다."):
    events, loop, bundle = Events(), loop_at(3), build().bundle()
    scene = bundle.beats[2 if current else 1]
    disclose(events, loop, scene, key="scene-3", text=scene.narration)
    for action in bundle.scene_actions:
        if action.beat != 3:
            continue
        disclose(events, loop, scene, key=f"action-3-{action.actor}-{action.action}",
                 text=fact if action.actor == "민석" else action.narration,
                 actor=action.actor, source_kind="statement" if reported else "scene")
    states = {c.code: NS(memory=[], plan=[]) for c in bundle.characters}
    day, model = LoopInteractor.__new__(LoopInteractor), Model(output)
    day._events, day._npc_llm, day._harness_on = events, model, True
    day._rules = NS(list=lambda _: [])
    day._notes = NS(upsert=lambda *args, **kwargs: None)
    day._loops = NS(npc_state=lambda _, code: states[code])
    return day._make_ambient(loop, bundle), model, events, states


@pytest.mark.parametrize("invented", ["민석이 좋아하는 거 있어.", "수첩에 기록 완료", "채연이 웃었어."])
def test_free_text_model_inventions_never_enter_ambient_or_memory(invented):
    result, _, events, states = ambient({"lines": [{"name": "민석", "line": invented}]})
    assert result is not None
    assert invented not in str(result)
    assert all(invented not in str(s.memory) for s in states.values())
    assert all(invented not in str(e) for e in events.rows if e.type != "harness_event")


def test_reported_action_cannot_enable_dialogue_requiring_observed_action():
    result, model, _, _ = ambient({"candidate_index": 0}, reported=True)
    assert result is None and not model.calls


def test_ambient_never_reuses_an_old_scene_as_current_dialogue():
    result, model, _, _ = ambient({"candidate_index": 0}, current=False)
    assert result is None and not model.calls
