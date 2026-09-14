"""Authored information revealed by an active question rule after actual scene actions."""


def question_reply(bundle, character, loop, observations, action):
    current = {o.observation_id: o for o in observations
               if o.loop_id == str(loop.id) and o.beat <= loop.beat}
    opportunities = {(o.beat, o.actor, o.action): o for o in bundle.scene_actions}
    absent = [c.name for c in bundle.characters if c.lost and loop.damage_level >= 3]
    for candidate in character.question_replies:
        if candidate.action != action or any(name in candidate.reply for name in absent):
            continue
        eligible = True
        for required in candidate.required_actions:
            source = current.get(f"{loop.id}:action-{required.beat}-{required.actor}-{required.action}")
            opportunity = opportunities.get((required.beat, required.actor, required.action))
            if (source is None or opportunity is None or source.verification != "observed"
                    or source.actor != required.actor or source.text != opportunity.narration):
                eligible = False
                break
        if eligible:
            return candidate.reply
    return None
