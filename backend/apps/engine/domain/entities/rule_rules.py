"""규칙 누적·충돌 감지 — 순수 함수 (부록 B)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    rule_id: str
    source: str  # user_choice | user_custom | monkey_paw
    target: str
    when_beat: int | None  # None = any
    effect: str  # suppress | enforce
    action: str
    created_loop: int


def _overlaps(a: int | None, b: int | None) -> bool:
    return a is None or b is None or a == b


def find_conflicts(existing: list[Rule], new: Rule) -> list[Rule]:
    """같은 target·(겹치는 beat)·같은 action에 suppress와 enforce가 공존하면 충돌.

    나중 규칙이 이기되 세계 손상 +1은 호출자가 반영한다.
    """
    return [
        r
        for r in existing
        if r.target == new.target
        and r.action == new.action
        and _overlaps(r.when_beat, new.when_beat)
        and r.effect != new.effect
    ]


DEFAULT_ENFORCE_BEAT = 3


def enforce_rules_on_plan(
    plan_beats: list[dict], rules: list[Rule], *, neutral_action: str
) -> list[dict]:
    """활성 규칙으로 계획을 기계 보정 — 결정적 강제 (순수 함수).

    suppress: 규칙 action과 일치하는 비트의 action을 중립 행동으로 치환.
    enforce: when_beat(없으면 비트 3)에 해당 action이 없으면 삽입/치환.
    생성 순서대로 적용 — 나중 규칙이 이긴다 (rules_for_npc 원칙과 동일).
    """
    beats = [dict(b) for b in plan_beats]
    for r in rules:
        if r.effect == "suppress":
            for b in beats:
                if b.get("action") == r.action and _overlaps(r.when_beat, b.get("beat")):
                    b["action"] = neutral_action
        elif r.effect == "enforce":
            if r.when_beat is None and any(b.get("action") == r.action for b in beats):
                continue  # any 규칙 — 어느 비트든 이미 하고 있으면 충분하다
            when = r.when_beat if r.when_beat is not None else DEFAULT_ENFORCE_BEAT
            slot = next((b for b in beats if b.get("beat") == when), None)
            if slot is None:
                beats.append({"beat": when, "action": r.action, "note": ""})
                beats.sort(key=lambda b: b.get("beat") or 0)
            else:
                slot["action"] = r.action
    return beats


def narration_with_rule_note(narration: str, rules: list[Rule], beat: int) -> str:
    """정적 내레이션이 suppress 규칙과 모순되면 결정적 보정 줄을 덧붙인다 (순수 함수).

    활성 규칙 전체를 검사해 매칭 규칙마다 한 줄 — 같은 대상의 중복 문구는 한 줄로 합친다.
    낮 내레이션과 밤 원인 체인(신의 정본)이 함께 쓴다.
    """
    noted_targets: list[str] = []
    for r in rules:
        if r.effect != "suppress":
            continue
        if r.when_beat is not None and r.when_beat != beat:
            continue
        if r.target in narration and r.action[:2] in narration and r.target not in noted_targets:
            noted_targets.append(r.target)
    if not noted_targets:
        return narration
    notes = [
        f"— 오늘은 다르다. {t}은(는) 그러지 않는다. 규칙이 막고 있다."
        for t in noted_targets
    ]
    return "\n".join([narration, *notes])


def rules_for_npc(rules: list[Rule], npc: str, beat: int) -> list[Rule]:
    """이 NPC·이 비트에 적용되는 규칙 (충돌 시 나중 규칙 우선)."""
    applicable = [
        r for r in rules if r.target == npc and (r.when_beat is None or r.when_beat == beat)
    ]
    winner: dict[tuple[str, int | None], Rule] = {}
    for r in applicable:  # 입력 순서 = 생성 순서 → 나중 것이 덮는다
        winner[(r.action, r.when_beat)] = r
    return list(winner.values())
