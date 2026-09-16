"""Execute finite public scene actions and audit actual rule opportunities."""

from apps.engine.app.dtos.event_log_dto import RuleExecutionEvent
from apps.engine.app.use_cases.public_observations import disclose

EXPLAIN_ACTION = "알고 있는 관찰을 설명한다"
SOURCE_ACTION = "소문의 알려진 출처를 밝힌다"
INFORMATION_ACTIONS = (EXPLAIN_ACTION, SOURCE_ACTION)


def execute_scene(event_log, loop, bundle, rules):
    beat = bundle.beats[loop.beat - 1]
    if not bundle.scene_actions:
        return beat
    narration = [beat.narration]
    illustrations = list(beat.illustrations)
    if loop.loop_n == 1 and beat.n == 1 and not any(c.playable and c.lost for c in bundle.characters):
        illustrations.extend(bundle.first_morning_illustrations)
    executed = {(e.rule_id, e.beat) for e in event_log.query(loop.attempt_id, loop_n=loop.loop_n)
                if e.type == "rule_execution"}
    shared_costs = {}
    absent = [c.name for c in bundle.characters if c.lost and loop.damage_level >= 3]
    for opportunity in bundle.scene_actions:
        if opportunity.beat != beat.n:
            continue
        if opportunity.actor in absent or any(name in opportunity.narration for name in absent):
            continue
        applicable = [r for r in rules if r.target == opportunity.actor
                      and (r.when_beat is None or r.when_beat == beat.n)
                      and (r.action == opportunity.action or r.action == EXPLAIN_ACTION
                           or (r.action == SOURCE_ACTION and opportunity.known_source is not None))]
        base_rules = [r for r in applicable if r.action == opportunity.action]
        winner = base_rules[-1] if base_rules else None
        if opportunity.dormant and not (winner is not None and winner.effect == "enforce"):
            # 잠재 기회 — enforce 규칙이 걸린 날에만 세계에 나타난다. 그 외에는 흔적도 없다.
            continue
        suppressed = winner is not None and winner.effect == "suppress"
        actual = None if suppressed else opportunity.action
        text = opportunity.suppressed_narration if suppressed else opportunity.narration
        narration.append(text)
        images = [] if suppressed else list(opportunity.illustrations)
        if loop.damage_level >= 3 and any(c.lost and c.name in opportunity.illustration_participants
                                         for c in bundle.characters):
            images = []
        illustrations.extend(images)
        observation = disclose(event_log, loop, beat,
            key=f"action-{beat.n}-{opportunity.actor}-{opportunity.action}", text=text,
            actor=opportunity.actor, illustrations=images,
            source_kind="rule_result" if winner else "scene", rule_id=winner.rule_id if winner else None)
        information_records = {}
        for rule in applicable:
            if (rule.rule_id, beat.n) in executed:
                continue
            result, action, evidence = "obeyed", actual, [observation.observation_id]
            if rule.action in INFORMATION_ACTIONS:
                same_action = [r for r in applicable if r.action == rule.action]
                if same_action[-1].effect != rule.effect:
                    result, action = "conflict", None
                elif rule.effect == "suppress" or suppressed:
                    action = None
                    result = "obeyed" if rule.effect == "suppress" else "not_evaluable"
                else:
                    # This action describes only the public opportunity the actor just experienced.
                    detail = (opportunity.known_source if rule.action == SOURCE_ACTION
                              else opportunity.explanation or opportunity.narration)
                    if rule.action not in information_records:
                        line = f"{opportunity.actor}: {detail}"
                        narration.append(line)
                        information_records[rule.action] = disclose(
                            event_log, loop, beat, key=f"rule-{beat.n}-{same_action[-1].rule_id}",
                            text=line, actor=opportunity.actor, source_kind="statement", rule_id=same_action[-1].rule_id)
                    info = information_records[rule.action]
                    evidence.append(info.observation_id)
                    action = rule.action
            elif winner and winner.effect != rule.effect:
                result = "conflict"
            side_effect = None
            cost_key = (opportunity.actor, action)
            if (rule.source == "monkey_paw" and action == EXPLAIN_ACTION and result == "obeyed"
                    and loop.budget_left > 0 and cost_key not in shared_costs):
                # A concrete cost of drawing public attention, not an invented model side effect.
                side_effect = f"{opportunity.actor}의 설명을 듣느라 다음에 말을 걸 여유가 줄었다."
                loop.budget_left = max(0, loop.budget_left - 1)
                cost = disclose(event_log, loop, beat, key=f"paw-cost-{beat.n}-{rule.rule_id}",
                                text=side_effect, actor=opportunity.actor, source_kind="rule_result", rule_id=rule.rule_id)
                narration.append(side_effect)
                shared_costs[cost_key] = cost
            if result == "obeyed" and cost_key in shared_costs:
                evidence.append(shared_costs[cost_key].observation_id)
            event_log.record(loop.attempt_id, RuleExecutionEvent(
                loop_n=loop.loop_n, beat=beat.n, rule_id=rule.rule_id,
                condition=f"{opportunity.actor}: {opportunity.action} 기회", actual_action=action,
                result=result, observation_ids=evidence, side_effect=side_effect))
            executed.add((rule.rule_id, beat.n))
    return beat.model_copy(update={"narration": " ".join(narration), "illustrations": illustrations})
