"""컴포지션 루트 — 포트에 어댑터를 주입하는 유일한 곳."""

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.game_state_orm import (
    LoopOrm,
    NightOrm,
    NpcStateOrm,
    RuleOrm,
)
from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.adapter.outbound.repositories.scene_transaction import SceneTransaction
from apps.engine.app.dtos.health_dto import HealthDTO, HealthModelsDTO
from apps.engine.app.ports.input.event_log_use_case import EventLogUseCase
from apps.engine.app.ports.input.health_use_case import HealthUseCase
from apps.engine.app.use_cases.event_log_interactor import EventLogInteractor
from apps.engine.app.use_cases.health_interactor import HealthInteractor
from apps.engine.app.use_cases.inspector_interactor import InspectorInteractor
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, SOURCE_ACTION
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.manager_interactor import ManagerInteractor
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.session_interactor import SessionInteractor
from apps.engine.dependencies.llm_factory import (
    get_core_llm,
    get_npc_llm,
)
from apps.engine.dependencies.scenario_factory import build_scenario
from core.matrix.grid_keymaker_secret_manager import get_settings
from core.matrix.grid_oracle_database_manager import get_session


def _scenario():
    return build_scenario(get_settings().scenario)


def get_event_log_use_case(session: Session = Depends(get_session)) -> EventLogUseCase:
    return EventLogInteractor(EventLogRepository(session))


def get_session_interactor(session: Session = Depends(get_session)):
    return SessionInteractor(
        attempts=AttemptRepository(session),
        event_log=EventLogRepository(session),
        scenario=_scenario(),
    )


def get_loop_interactor(session: Session = Depends(get_session)):
    s = get_settings()
    scenario = _scenario()
    return LoopInteractor(
        attempts=AttemptRepository(session),
        loops=LoopRepository(session),
        notes=NoteRepository(session),
        rules=RuleRepository(session),
        event_log=EventLogRepository(session),
        scenario=scenario,
        npc_llm=get_npc_llm(),
        core_llm=get_core_llm(),
        manager=ManagerInteractor(
            core_llm=get_core_llm(), scenario=scenario,
            harness_on=s.system_harness == "on",
        ),
        harness_on=s.system_harness == "on",
        age7_on=s.npc_age7_policy == "on",
        paw_reason_ab_on=s.paw_reason_ab == "on",
        loop_cls=LoopOrm, npc_state_cls=NpcStateOrm, rule_cls=RuleOrm,
        scene_transaction=SceneTransaction(session),
    )


def get_night_interactor(session: Session = Depends(get_session)):
    s = get_settings()
    return NightInteractor(
        attempts=AttemptRepository(session),
        loops=LoopRepository(session),
        notes=NoteRepository(session),
        rules=RuleRepository(session),
        nights=NightRepository(session),
        event_log=EventLogRepository(session),
        scenario=_scenario(),
        core_llm=get_core_llm(),
        harness_on=s.system_harness == "on",
        cookie_ab_on=s.cookie_ab == "on",
        night_cls=NightOrm,
    )


def get_intervention_interactor(session: Session = Depends(get_session)):
    s = get_settings()
    scenario = _scenario()
    bundle = scenario.bundle()
    return InterventionInteractor(
        attempts=AttemptRepository(session),
        loops=LoopRepository(session),
        notes=NoteRepository(session),
        rules=RuleRepository(session),
        nights=NightRepository(session),
        event_log=EventLogRepository(session),
        core_llm=get_core_llm(),
        action_vocab=bundle.action_vocab,
        world_context=bundle.surface_summary,
        question_rule_targets=[c.name for c in bundle.characters if c.question_replies],
        target_names=[c.name for c in bundle.characters if c.playable],
        harness_on=s.system_harness == "on",
        rule_cls=RuleOrm,
        rule_templates=[
            {"target": opportunity.actor, "when_beat": opportunity.beat, "effect": "enforce",
             "action": action, "label": f"{opportunity.actor}: {action}"}
            for opportunity in bundle.scene_actions
            for action in ([EXPLAIN_ACTION, SOURCE_ACTION, opportunity.action]
                           if opportunity.known_source is not None else [EXPLAIN_ACTION, opportunity.action])
        ],
    )


def get_inspector(session: Session = Depends(get_session)):
    return InspectorInteractor(
        attempts=AttemptRepository(session),
        rules=RuleRepository(session),
        event_log=EventLogRepository(session),
        inspector_token=get_settings().inspector_token,
        notes=NoteRepository(session),
    )


def get_health_use_case(session: Session = Depends(get_session)) -> HealthUseCase:
    settings = get_settings()

    def db_ping() -> bool:
        session.execute(text("SELECT 1"))
        return True

    return HealthInteractor(
        scenario=_scenario(),
        harness=settings.system_harness,
        models=HealthModelsDTO(
            npc=f"{settings.npc_llm_provider}:{settings.npc_llm_model}",
            core=f"{settings.core_llm_provider}:{settings.core_llm_model}",
            embedding=settings.embedding_provider,
        ),
        db_ping=db_ping,
    )
