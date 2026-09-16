"""Give participants the experience they acquired, without reading player notes."""

from apps.engine.domain.entities.npc_memory import add_memory, visible_memories
from apps.engine.app.use_cases.question_replies import actions_occurred


def context_ids(bundle, character, memory, damage_level):
    return set(evidence_reference_map(bundle, character, memory, damage_level).values())


def evidence_reference_map(bundle, character, memory, damage_level):
    """Short prompt references resolve to persistent sources before any memory is saved."""
    absent = tuple(c.name for c in bundle.characters if c.lost and damage_level >= 3)
    knowledge = [k for k in character.knowledge
                 if not any(name in k.text or name == k.source for name in absent)]
    visible = visible_memories(memory, excluded_names=absent)
    return {**{f"k{i}": k.id for i, k in enumerate(knowledge, 1)},
            **{f"m{i}": m["id"] for i, m in enumerate(visible, 1)}}


def resolve_output_sources(output, bundle, character, memory, damage_level):
    references = evidence_reference_map(bundle, character, memory, damage_level)
    output.evidence_ids = [references.get(key, key) for key in output.evidence_ids]
    tool = getattr(output, "tool_call", None)
    if tool and tool.statement_id is not None:
        tool.statement_id = references.get(tool.statement_id, tool.statement_id)


def response_sources(memory, evidence_ids):
    """Uncited model text may depend on any supplied memory; never restore it after deletion."""
    visible = visible_memories(memory)
    ids = {m["id"] for m in visible}
    return [key for key in evidence_ids if key in ids] if evidence_ids else [m["id"] for m in visible]


def learn_scene(bundle, loop, states, observations):
    current = {o.observation_id: o for o in observations
               if o.loop_id == str(loop.id) and o.beat == loop.beat}
    absent = tuple(c.name for c in bundle.characters if c.lost and loop.damage_level >= 3)
    for state in states:
        if state.name in absent:
            continue
        memory = list(state.memory or [])
        broadcast = current.get(f"{loop.id}:broadcast-{loop.beat}")
        if broadcast and not any(name in broadcast.text for name in absent):
            memory = add_memory(memory, memory_id=broadcast.observation_id, beat=loop.beat,
                kind="들은 방송", text=broadcast.text, speaker=broadcast.actor,
                listeners=[state.name])
        for action in bundle.scene_actions:
            if action.beat != loop.beat or (state.name != action.actor and state.name not in action.witnesses):
                continue
            observation = current.get(f"{loop.id}:action-{loop.beat}-{action.actor}-{action.action}")
            if observation is None:
                continue
            occurred = observation.verification == "observed" and observation.text == action.narration
            if state.name == action.actor:
                kind = "내가 한 일" if occurred else "하지 않은 일"
                detail = (action.explanation or action.narration) if occurred else f"오늘은 {action.action} 행동을 하지 않았다."
                account = next((a for a in action.experience_accounts if occurred
                                and actions_occurred(bundle, loop, observations, a.required_actions)), None)
                if account:
                    detail = account.text
                if occurred and action.known_source:
                    detail += " " + action.known_source
            else:
                kind, detail = "직접 본 일", observation.text
            if any(name in detail for name in absent):
                continue
            memory = add_memory(memory, memory_id=observation.observation_id, beat=loop.beat,
                kind=kind, text=detail, speaker=action.actor, listeners=[state.name],
                source_ids=[f"{loop.id}:action-{r.beat}-{r.actor}-{r.action}" for r in account.required_actions]
                if state.name == action.actor and account else [])
            if occurred:
                spoken_details = {f"{action.actor}: {line}" for line in (action.known_source, action.explanation or action.narration) if line}
                for speech in current.values():
                    if (speech.source_kind != "statement" or not speech.rule_id
                            or speech.actor != action.actor or speech.text not in spoken_details
                            or any(name in speech.text for name in absent)):
                        continue
                    memory = add_memory(memory, memory_id=speech.observation_id, beat=loop.beat,
                        kind="내가 한 말" if state.name == action.actor else "들은 말",
                        text=speech.text, speaker=action.actor, listeners=[state.name],
                        source_ids=[observation.observation_id])
        for index, fragment in enumerate(bundle.fragments):
            if fragment.source_kind != "statement" or (state.name != fragment.actor and state.name not in fragment.witnesses):
                continue
            speech = current.get(f"{loop.id}:fragment-{index}")
            if speech and not any(name in speech.text for name in absent):
                memory = add_memory(memory, memory_id=speech.observation_id, beat=loop.beat,
                    kind="내가 한 말" if state.name == fragment.actor else "들은 말",
                    text=speech.text, speaker=fragment.actor, listeners=[state.name])
        state.memory = memory


def context_output_check(bundle, character, memory, damage_level):
    references = evidence_reference_map(bundle, character, memory, damage_level)
    allowed = set(references) | set(references.values())
    targets = {ref for c in bundle.characters if c.playable and not (c.lost and damage_level >= 3)
               for ref in (c.code, c.name)}

    def check(output):
        if any(key not in allowed for key in output.evidence_ids):
            return "evidence_ids: 제공된 지식·기억 ID만 사용할 수 있다"
        tool = getattr(output, "tool_call", None)
        if tool and (tool.target not in targets or tool.target in (character.code, character.name)):
            return "tool_target: 현재 대화 가능한 다른 인물만 선택한다"
        if tool and tool.statement_id is not None and tool.statement_id not in allowed:
            return "statement_id: 오늘 직접 들은 발언의 ID만 사용할 수 있다"
        return None
    return check
