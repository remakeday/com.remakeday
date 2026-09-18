"""Execute finite public scene actions and audit actual rule opportunities."""

from apps.engine.app.dtos.event_log_dto import RuleExecutionEvent
from apps.engine.app.dtos.line_dto import LineDTO
from apps.engine.app.use_cases.explanation_grounding import explanation_line
from apps.engine.app.use_cases.public_observations import disclose, public_observations
from apps.engine.domain.entities.rule_rules import PAW_EFFECT_SOURCE

EXPLAIN_ACTION = "알고 있는 관찰을 설명한다"
SOURCE_ACTION = "소문의 알려진 출처를 밝힌다"
INFORMATION_ACTIONS = (EXPLAIN_ACTION, SOURCE_ACTION)

# 숨은 규칙이 "의도대로" 실행됐을 때의 실제 행동 — enforce는 행동 발생, suppress는 억제
_INTENDED_ACTION = {"enforce": lambda effect: effect.action, "suppress": lambda effect: None}


def _wish_fulfilled(bundle, rules, outcomes, observation):
    """관찰 문장을 가진 소원의 숨은 규칙이 이 회차에 전부 의도대로 실행됐는가 (스펙 §3 공개 조건)."""
    wish = next((w for w in bundle.paw_wishes if w.observation == observation), None)
    if wish is None:
        return False
    for effect in wish.effects:
        # 소원 장면(reveal)보다 앞선 비트의 억제(예: ① 아침 배급 억제)는 받는 날엔 실행될 수 없다 — 공개 판정에서 뺀다.
        if effect.beat < wish.reveal.beat:
            continue
        rule = next((r for r in rules if r.source == PAW_EFFECT_SOURCE and r.target == effect.actor
                     and r.action == effect.action and r.when_beat == effect.beat and r.effect == effect.effect), None)
        expected = ("obeyed", _INTENDED_ACTION[effect.effect](effect))
        if rule is None or outcomes.get((rule.rule_id, effect.beat)) != expected:
            return False
    return True


def _scene_line(loop, beat, illustrations):
    """첫 줄은 장면 서술 — observation_id 키는 _disclose_scene의 scene-{n}과 같다."""
    return LineDTO(kind="scene", text=beat.narration, observation_id=f"{loop.id}:scene-{beat.n}",
                   image_id=illustrations[0].image_id if illustrations else None)


def execute_scene(event_log, loop, bundle, rules, on_action=None):
    """on_action(opportunity): 억제되지 않은 행동의 관찰이 이번 호출에서 처음 생겼을 때만 호출된다.
    돌려주는 beat의 lines가 대사창 줄 레코드, narration은 그 text를 이어 붙인 것."""
    beat = bundle.beats[loop.beat - 1]
    if not bundle.scene_actions:
        return beat.model_copy(update={"lines": [_scene_line(loop, beat, beat.illustrations)]})
    illustrations = list(beat.illustrations)
    if loop.loop_n == 1 and beat.n == 1 and not any(c.playable and c.lost for c in bundle.characters):
        illustrations.extend(bundle.first_morning_illustrations)
    lines = [_scene_line(loop, beat, illustrations)]
    outcomes = {(e.rule_id, e.beat): (e.result, e.actual_action)
                for e in event_log.query(loop.attempt_id, loop_n=loop.loop_n) if e.type == "rule_execution"}
    executed = set(outcomes)
    disclosed = {o.observation_id for o in public_observations(event_log, loop.attempt_id)}
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
        images = [] if suppressed else list(opportunity.illustrations)
        if loop.damage_level >= 3 and any(c.lost and c.name in opportunity.illustration_participants
                                         for c in bundle.characters):
            images = []
        illustrations.extend(images)
        observation = disclose(event_log, loop, beat,
            key=f"action-{beat.n}-{opportunity.actor}-{opportunity.action}", text=text,
            actor=opportunity.actor, illustrations=images,
            source_kind="rule_result" if winner else "scene", rule_id=winner.rule_id if winner else None)
        lines.append(LineDTO(kind="rule_result" if winner else "action", text=text,
                             image_id=images[0].image_id if images else None, observation_id=observation.observation_id))
        if on_action is not None and not suppressed and observation.observation_id not in disclosed:
            disclosed.add(observation.observation_id)
            on_action(opportunity)
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
                              else explanation_line(bundle, opportunity))
                    if rule.action not in information_records:
                        line = f"{opportunity.actor}: {detail}"
                        information_records[rule.action] = disclose(
                            event_log, loop, beat, key=f"rule-{beat.n}-{same_action[-1].rule_id}",
                            text=line, actor=opportunity.actor, source_kind="statement", rule_id=same_action[-1].rule_id)
                        lines.append(LineDTO(kind="statement", speaker=opportunity.actor, text=line,
                                             observation_id=information_records[rule.action].observation_id))
                    info = information_records[rule.action]
                    evidence.append(info.observation_id)
                    action = rule.action
            elif winner and winner.effect != rule.effect:
                result = "conflict"
            outcomes[(rule.rule_id, beat.n)] = (result, action)
            side_effect = None
            if (rule.source == PAW_EFFECT_SOURCE and rule.hidden_side_effect and result == "obeyed"
                    and _wish_fulfilled(bundle, rules, outcomes, rule.hidden_side_effect)):
                # 반대 사건이 전부 실제로 일어난 날만 문장을 남긴다 — 노트에 거짓 문장이 들어가지 않는다.
                side_effect = rule.hidden_side_effect
                revealed = disclose(event_log, loop, beat, key=f"paw-effect-{beat.n}-{rule.rule_id}",
                                text=side_effect, source_kind="rule_result", rule_id=rule.rule_id)
                lines.append(LineDTO(kind="paw_effect", text=side_effect, observation_id=revealed.observation_id))
                evidence.append(revealed.observation_id)
            event_log.record(loop.attempt_id, RuleExecutionEvent(
                loop_n=loop.loop_n, beat=beat.n, rule_id=rule.rule_id,
                condition=f"{opportunity.actor}: {opportunity.action} 기회", actual_action=action,
                result=result, observation_ids=evidence, side_effect=side_effect))
            executed.add((rule.rule_id, beat.n))
    return beat.model_copy(update={"narration": " ".join(line.text for line in lines),
                                  "illustrations": illustrations, "lines": lines})
