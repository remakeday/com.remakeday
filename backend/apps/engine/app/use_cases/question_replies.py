"""Authored information revealed by an active question rule after actual scene actions."""


def actions_occurred(bundle, loop, observations, required_actions):
    current = {o.observation_id: o for o in observations
               if o.loop_id == str(loop.id) and o.beat <= loop.beat}
    opportunities = {(o.beat, o.actor, o.action): o for o in bundle.scene_actions}
    for required in required_actions:
        source = current.get(f"{loop.id}:action-{required.beat}-{required.actor}-{required.action}")
        opportunity = opportunities.get((required.beat, required.actor, required.action))
        if (source is None or opportunity is None or source.verification != "observed"
                or source.actor != required.actor or source.text != opportunity.narration):
            return False
    return True


def question_reply(bundle, character, loop, observations, action, *, hidden_ids=frozenset()):
    absent = [c.name for c in bundle.characters if c.lost and loop.damage_level >= 3]
    if any(f"{loop.id}:action-{r.beat}-{r.actor}-{r.action}" in hidden_ids
           for candidate in character.question_replies if candidate.action == action
           for r in candidate.required_actions):
        return None  # A weaker fallback must not turn forgotten activity into a denial.
    for candidate in character.question_replies:
        if candidate.action != action or any(name in candidate.reply for name in absent):
            continue
        if actions_occurred(bundle, loop, observations, candidate.required_actions):
            return candidate.reply
    return None
