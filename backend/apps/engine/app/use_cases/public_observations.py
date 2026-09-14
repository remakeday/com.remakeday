"""Persist and retrieve only records actually disclosed by the day use case."""

from apps.engine.app.dtos.event_log_dto import ObservationEvent
from apps.engine.app.dtos.observation_dto import ObservationDTO


def public_observations(event_log, attempt_id, *, through_loop=None):
    return [e.observation for e in event_log.query(attempt_id)
            if e.type == "observation" and (through_loop is None or e.loop_n <= through_loop)]


def disclose(event_log, loop, beat, *, key, text, actor=None, source_kind="scene",
             illustrations=(), rule_id=None):
    observation_id = f"{loop.id}:{key}"
    existing = next((o for o in public_observations(event_log, loop.attempt_id)
                     if o.observation_id == observation_id), None)
    if existing:
        return existing
    observation = ObservationDTO(
        observation_id=observation_id, attempt_id=str(loop.attempt_id), loop_id=str(loop.id),
        loop_n=loop.loop_n, beat=beat.n, scene_id=f"{loop.id}:beat-{beat.n}",
        scene_title=beat.title, actor=actor, text=text, source_kind=source_kind,
        verification="reported" if source_kind == "statement" else "observed",
        illustrations=list(illustrations), rule_id=rule_id,
    )
    event_log.record(loop.attempt_id, ObservationEvent(loop_n=loop.loop_n, observation=observation))
    return observation
