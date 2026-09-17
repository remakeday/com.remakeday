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


def memory_references(memory: list) -> dict[str, dict]:
    """관리자 점검용 짧은 참조(m1…) → 보이는 기억. 삭제로 번호가 밀리지 않게 점검 시작 때 한 번 고정한다."""
    return {f"m{index}": m for index, m in enumerate(visible_memories(memory), 1)}


_MIN_QUOTE_LENGTH = 6


def _by_reference(references: dict[str, dict], target: str) -> set[str]:
    return {references[target]["id"]} if target in references else set()


def _by_memory_id(references: dict[str, dict], target: str) -> set[str]:
    """원래 ID, 또는 모델이 회차 접두어("{loop_id}:")를 뗀 ID."""
    return {m["id"] for m in references.values() if m["id"] == target or m["id"].endswith(":" + target)}


def _by_verbatim_quote(references: dict[str, dict], target: str) -> set[str]:
    """기억 원문을 그대로 옮긴 인용만. 뜻풀이·요약은 어느 기억인지 확정할 수 없어 매칭하지 않는다."""
    if len(target) < _MIN_QUOTE_LENGTH:
        return set()
    return {m["id"] for m in references.values() if target in m["text"]}


_REFERENCE_RESOLVERS = (_by_reference, _by_memory_id, _by_verbatim_quote)


def resolve_memory_reference(references: dict[str, dict], target: str) -> str | None:
    """앞 단계에서 찾으면 멈춘다. 후보가 둘 이상이면 오삭제를 막기 위해 적용하지 않는다."""
    target = target.strip()
    for resolver in _REFERENCE_RESOLVERS:
        ids = resolver(references, target)
        if ids:
            return next(iter(ids)) if len(ids) == 1 else None
    return None
