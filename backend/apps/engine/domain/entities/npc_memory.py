"""Source-addressed day memories stored in the existing JSON memory field.

Deletion leaves a tombstone so replaying an observation cannot restore it.
Replies derived from a deleted source are hidden too; an independent new
experience can teach the same fact again. Older string memories remain readable.
"""


def memory_entries(memory: list) -> list[dict]:
    return [dict(item) if isinstance(item, dict) else {
        "id": f"legacy-{index}", "beat": 0, "kind": "dialogue", "text": item,
        "speaker": None, "listeners": [], "source_ids": [], "forgotten": False,
    } for index, item in enumerate(memory)]


def hidden_memory_ids(memory: list) -> set[str]:
    entries = memory_entries(memory)
    hidden = {m["id"] for m in entries if m.get("forgotten")}
    while True:
        derived = {m["id"] for m in entries if hidden.intersection(m.get("source_ids", []))}
        if derived <= hidden:
            return hidden
        hidden |= derived


def visible_memories(memory: list, *, excluded_names: tuple[str, ...] = ()) -> list[dict]:
    hidden = hidden_memory_ids(memory)
    return [m for m in memory_entries(memory) if m["id"] not in hidden
            and not any(name in m["text"] or name == m.get("speaker") for name in excluded_names)]


def add_memory(memory: list, *, memory_id: str, beat: int, kind: str, text: str,
               speaker: str | None, listeners: list[str], source_ids: list[str] | None = None) -> list[dict]:
    entries = memory_entries(memory)
    if any(m["id"] == memory_id for m in entries):
        return entries
    return entries + [{
        "id": memory_id, "beat": beat, "kind": kind, "text": text,
        "speaker": speaker, "listeners": list(listeners),
        "source_ids": list(source_ids or []), "forgotten": False,
    }]


def forget_memory(memory: list, memory_id: str) -> tuple[list[dict], bool]:
    entries = memory_entries(memory)
    visible_ids = {m["id"] for m in visible_memories(entries)}
    if memory_id not in visible_ids:
        return entries, False
    return [dict(m, forgotten=True) if m["id"] == memory_id else m for m in entries], True
