from apps.engine.app.dtos.llm_output_dto import AgentOutput
from apps.engine.app.use_cases.harness import unknown_person_check


def test_regulation_and_ordinary_predicates_are_not_invented_people():
    check = unknown_person_check(["준", "민석"], fields=["reply"])
    for reply in ["규정이야. 방송에서 말했어.", "내 차례야.", "약속이야.", "걱정이야."]:
        assert check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0)) is None


def test_explicit_new_speaker_still_rejected():
    check = unknown_person_check(["준", "민석"], fields=["reply"])
    assert check(AgentOutput(reply="영수가 말했다고 했어.", suspicion_delta=0, trust_delta=0))


def test_one_syllable_name_with_familiar_suffix_matches_roster():
    check = unknown_person_check(["준", "민석"], fields=["reply"])
    for reply in ["준이가 말했어.", "준이가 그랬어.", "내 친구는 준이야."]:
        assert check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0)) is None


def test_valid_evidence_in_display_brackets_does_not_regenerate_good_reply():
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    from apps.engine.app.use_cases.harness import run_with_harness
    from apps.engine.app.use_cases.npc_context import context_output_check
    from apps.scenarios.scenario_a.adapter import build
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == "minseok")
    model = FakeLLM([{"reply": "방송에서 들었어.", "evidence_ids": ["[minseok-band-rule]"],
                     "suspicion_delta": 0, "trust_delta": 0}])
    output, report = run_with_harness(model, [], AgentOutput, role="agent",
        fact_checks=[context_output_check(bundle, char, [], 0)])
    assert output is not None and output.reply == "방송에서 들었어."
    assert report.attempts == 1 and output.evidence_ids == ["minseok-band-rule"]


def test_short_evidence_reference_keeps_canonical_memory_dependency_after_deletion():
    from apps.engine.app.use_cases.npc_context import context_output_check, resolve_output_sources, response_sources
    from apps.engine.app.use_cases.game_support import build_agent_messages
    from apps.engine.domain.entities.npc_memory import add_memory, forget_memory, visible_memories
    from apps.scenarios.scenario_a.adapter import build
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == "eunsang")
    source = "48c6351a-a6cd-4990-b533-deadecc6e558:action-2-은상-소문을 낸다"
    memory = add_memory([], memory_id=source, beat=2, kind="들은 말", text="준이 내게 말했어.",
                        speaker="준", listeners=["은상"])
    messages = build_agent_messages(bundle, char, suspicion=0, trust=0, opposite=False,
        rules_text="", memory=memory, user_text="누가 말했어?", loop_n=1, age7_on=True)
    assert '"id": "m1"' in messages[0].content and source not in messages[0].content
    out = AgentOutput(reply="준이 말했어.", suspicion_delta=0, trust_delta=0, evidence_ids=["m1"],
        tool_call={"name": "ask_npc", "target": "준", "question": "네가 말했지?", "statement_id": "m1"})
    assert context_output_check(bundle, char, memory, 0)(out) is None
    resolve_output_sources(out, bundle, char, memory, 0)
    assert out.evidence_ids == [source] and out.tool_call.statement_id == source
    memory = add_memory(memory, memory_id="reply", beat=2, kind="대화", text=out.reply,
        speaker=char.name, listeners=[char.name], source_ids=response_sources(memory, out.evidence_ids))
    memory, _ = forget_memory(memory, source)
    assert visible_memories(memory) == []


def test_unavailable_short_evidence_reference_is_rejected():
    from apps.engine.app.use_cases.npc_context import context_output_check
    from apps.scenarios.scenario_a.adapter import build
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == "minseok")
    out = AgentOutput(reply="봤어.", suspicion_delta=0, trust_delta=0, evidence_ids=["m1"])
    assert context_output_check(bundle, char, [], 0)(out) is not None


def _number_check(code, memory, question, field="reply", beat=1):
    from apps.engine.app.use_cases.npc_context import grounded_number_check
    from apps.scenarios.scenario_a.adapter import build
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == code)
    return grounded_number_check(bundle, char, memory, 0, question=question, beat=beat, field=field)


def _said(text, loop_beat=2, speaker="준"):
    return [{"id": "a", "beat": loop_beat, "kind": "내가 한 일", "text": text, "speaker": speaker,
             "listeners": [speaker], "source_ids": [], "forgotten": False}]


def test_number_absent_from_memory_and_question_is_rejected():
    """테스터9 F14 — 손목띠 숫자 값은 어디에도 없는데 '내 거는 7이야'를 지어냈다."""
    check = _number_check("jun", _said("불빛에 비춰 봤어. 숫자가 써 있잖아."), "네 손목띠 숫자 읽어 줄래?")
    violation = check(AgentOutput(reply="내 거는 7이야. 채연이는 5야.", suspicion_delta=0, trust_delta=0))
    assert violation and "unsupported_number" in violation and "7" in violation


def test_number_in_memory_question_or_numeral_word_is_allowed():
    check = _number_check("jun", _said("쟁반 2개가 남았어. 하나는 채연 거야."), "3번 봤어?")
    for reply in ["쟁반 2개 남았어.", "응, 3번 봤어.", "1개는 채연 거야.", "숫자는 잘 모르겠어."]:
        assert check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0)) is None


def test_number_check_reads_the_ask_npc_answer_field():
    from apps.engine.app.dtos.llm_output_dto import AskNpcOutput
    check = _number_check("jun", [], "민석: 네 띠 숫자 뭐야?", field="answer")
    assert check(AskNpcOutput(answer="9야."))


def test_public_scene_text_numbers_are_grounded():
    """B등급 리뷰 — 장면 제목 '기상 — 7:12'은 인물도 아는 공개 값이다. '7:12'와 '7시 12분'은 같은 숫자다."""
    check = _number_check("minseok", [], "오늘 몇 시에 일어났어?", beat=1)
    for reply in ["7시 12분에 일어났어.", "7:12에 일어났어.", "7시쯤 일어났어."]:
        assert check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0)) is None, reply


def test_public_scene_numbers_do_not_leak_unrelated_values():
    """공개 텍스트를 넣어도 어디에도 없는 값(7시 13분·질문 숫자의 19시 변환)은 계속 거부한다."""
    check = _number_check("minseok", [], "7시에 뭐 했어?", beat=6)
    for reply in ["7시 13분에 일어났어.", "19시에 배급 받았어.", "내 거는 12야."]:
        violation = check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0))
        assert violation and "unsupported_number" in violation, reply


def _denial(reply):
    from apps.engine.app.use_cases.npc_context import own_action_denial_check
    memory = _said("오늘 방송실에 갔어. 문 앞까지 갔다가 돌아왔어.", 5, "민석")
    check = own_action_denial_check(memory, names=["채연", "민석", "은상", "준", "충식", "관리자"])
    return check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0))


def test_denial_about_another_person_or_another_day_is_allowed():
    """B등급 리뷰 — 부정 절의 주어가 다른 인물이거나 시점이 오늘이 아니면 내 행동 부정이 아니다."""
    for reply in ["채연이는 방송실에 안 갔어. 나만 갔어.",
                  "어제는 방송실에 안 갔어. 어제 얘기는 잘 몰라.",
                  "준은 방송실에 가지 않았어.",
                  "나는 갔는데 은상이는 방송실까지는 안 갔어.",
                  "방송실 안에는 안 들어갔어."]:
        assert _denial(reply) is None, reply


def test_own_denial_still_rejected_next_to_other_names_or_days():
    for reply in ["나는 오늘 방송실에 가지 않았어.",
                  "어제는 갔는데 오늘은 방송실에 안 갔어.",
                  "채연이랑 나는 방송실에 안 갔어.",
                  "채연이는 잤어. 나도 방송실에 안 갔어.",
                  "기준이 없어서 방송실에 안 갔어."]:
        violation = _denial(reply)
        assert violation and "own_action_denial" in violation, reply


def test_denying_a_place_the_actor_remembers_going_to_is_rejected():
    """테스터9 F14 — 기억 '오늘 방송실에 갔어'가 있는데 '방송실에 가지 않았어'라고 답했다."""
    from apps.engine.app.use_cases.npc_context import own_action_denial_check
    check = own_action_denial_check(_said("오늘 방송실에 갔어. 문 앞까지 갔다가 돌아왔어.", 5, "민석"), names=["민석", "채연"])
    for reply in ["나는 오늘 방송실에 가지 않았어.", "오늘은 방송실에 직접 가지 않았어.",
                  "방송실까지는 안 갔어.", "실제로 방송실에 간 적은 없어."]:
        violation = check(AgentOutput(reply=reply, suspicion_delta=0, trust_delta=0))
        assert violation and "own_action_denial" in violation, reply


def test_place_denial_is_allowed_when_not_in_own_actions():
    from apps.engine.app.use_cases.npc_context import own_action_denial_check
    seen = [{**_said("민석이 방송실에 갔어.", 5, "민석")[0], "kind": "직접 본 일"}]
    for memory in (seen, _said("오늘 방송실에 갔어.", 5, "민석")):
        check = own_action_denial_check(memory, names=["민석"])
        assert check(AgentOutput(reply="방송실까지 갔다가 돌아왔어. 안에는 안 들어갔어.", suspicion_delta=0, trust_delta=0)) is None
    assert own_action_denial_check(seen, names=["민석"])(AgentOutput(reply="나는 방송실에 가지 않았어.", suspicion_delta=0, trust_delta=0)) is None
