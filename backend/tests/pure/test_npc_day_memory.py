"""Memory deletion cannot be undone by related dialogue or observation replay."""

from apps.engine.domain.entities.npc_memory import add_memory, forget_memory, visible_memories
from apps.engine.domain.entities.npc_rules import NpcMemory, remember


def test_today_conversation_survives_more_than_three_lines():
    memory = NpcMemory()
    for line in ["내 이름은 도윤", "응", "춥다", "담요 있어", "같이 앉아"]:
        memory = remember(memory, line)
    assert memory.turns[0] == "내 이름은 도윤"


def test_deletion_masks_dependent_reply_but_keeps_other_experiences():
    memory = []
    for key, text, sources in [
        ("action-1", "내가 수첩에 적었다", []),
        ("reply-1", "적은 이유를 말함", ["action-1"]),
        ("sound-1", "복도 소리를 들음", []),
    ]:
        memory = add_memory(memory, memory_id=key, beat=1, kind="observed", text=text,
                            speaker="민석", listeners=["민석"], source_ids=sources)
    memory, applied = forget_memory(memory, "action-1")
    assert applied
    assert [m["id"] for m in visible_memories(memory)] == ["sound-1"]


def test_replaying_deleted_source_cannot_restore_it_but_new_experience_can():
    args = dict(beat=1, kind="observed", text="문에 붙은 표시", speaker=None, listeners=["준"])
    memory = add_memory([], memory_id="sighting-1", **args)
    memory, _ = forget_memory(memory, "sighting-1")
    memory = add_memory(memory, memory_id="sighting-1", **args)
    assert visible_memories(memory) == []
    memory = add_memory(memory, memory_id="sighting-2", **args)
    assert [m["id"] for m in visible_memories(memory)] == ["sighting-2"]


def test_invalid_deletion_is_not_applied_and_legacy_strings_remain_readable():
    memory, applied = forget_memory(["유저: 아까 이름 말했어"], "missing")
    assert not applied
    assert visible_memories(memory)[0]["text"] == "유저: 아까 이름 말했어"


def _memories():
    memory = []
    for key, text in [
        ("loop-uuid:broadcast-1", "배급을 시작합니다."),
        ("loop-uuid:action-3-민석-기록한다", "채연이가 남긴 배급을 수첩에 적었어."),
        ("loop-uuid:rule-3-R1", "채연: 쟁반 밀었어. 지금은 안 먹고 싶어."),
        ("loop-uuid:u-abc", "플레이어: 배급은 어디서 오는 거야?\n준: 몰라."),
        ("loop-uuid:ambient-3-0", "채연: 민석아, 뭘 적어?"),
    ]:
        memory = add_memory(memory, memory_id=key, beat=3, kind="observed", text=text,
                            speaker=None, listeners=["민석"])
    return memory


def test_manager_memory_reference_resolution_table():
    """테스터11 O5 — 짧은 참조·원래 ID·회차 접두어 없는 ID·원문 인용만 받고 뜻풀이는 거부한다."""
    from apps.engine.domain.entities.npc_memory import memory_references, resolve_memory_reference
    refs = memory_references(_memories())
    assert list(refs) == ["m1", "m2", "m3", "m4", "m5"]
    cases = [
        ("m2", "loop-uuid:action-3-민석-기록한다"),
        (" m3 ", "loop-uuid:rule-3-R1"),
        ("loop-uuid:u-abc", "loop-uuid:u-abc"),
        ("action-3-민석-기록한다", "loop-uuid:action-3-민석-기록한다"),  # 모델이 회차 UUID를 뗀 경우
        ("배급은 어디서 오는 거야?", "loop-uuid:u-abc"),  # 기억 원문 그대로의 인용(유일)
        ("어제 밤에 민석이와 나눈 대화 내용", None),  # 뜻풀이 — 오매칭 위험이라 거부
        ("검진을 받으며 느낀 감정이나 상황에 대한 기억", None),
        ("R1", None),  # 규칙 번호는 기억 ID가 아니다
        ("m9", None),
        ("채연", None),  # 짧은 인용은 여러 기억에 걸린다
        ("배급", None),
        ("", None),
    ]
    assert [(target, resolve_memory_reference(refs, target)) for target, _ in cases] == cases


def test_manager_reference_is_ambiguous_quote_safe_and_skips_forgotten():
    from apps.engine.domain.entities.npc_memory import memory_references, resolve_memory_reference
    memory, _ = forget_memory(_memories(), "loop-uuid:broadcast-1")
    refs = memory_references(memory)
    assert "loop-uuid:broadcast-1" not in {m["id"] for m in refs.values()}
    assert resolve_memory_reference(refs, "broadcast-1") is None
    assert resolve_memory_reference(refs, "채연이가 남긴 배급") == "loop-uuid:action-3-민석-기록한다"
    assert resolve_memory_reference(refs, "지금은 안 먹고 싶어") == "loop-uuid:rule-3-R1"
