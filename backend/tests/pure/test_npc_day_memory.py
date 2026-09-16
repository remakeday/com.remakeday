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
