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
