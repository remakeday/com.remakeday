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
from apps.engine.adapter.outbound.oauth.google_oauth_client import GoogleOAuthClient
from apps.engine.adapter.outbound.repositories.scene_transaction import (
    AttemptTransaction,
    NightTransaction,
    SceneTransaction,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.adapter.outbound.security.session_token_signer import SessionTokenSigner
from apps.engine.app.dtos.auth_dto import DevAccountDTO
from apps.engine.app.ports.input.auth_use_case import AuthUseCase
from apps.engine.app.ports.input.event_log_use_case import EventLogUseCase
from apps.engine.app.ports.input.health_use_case import HealthUseCase
from apps.engine.app.use_cases.attempt_access_interactor import AttemptAccessInteractor
from apps.engine.app.use_cases.auth_interactor import AuthInteractor
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
    get_alternative_rank,
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
    s = get_settings()
    return SessionInteractor(
        attempts=AttemptRepository(session),
        event_log=EventLogRepository(session),
        scenario=_scenario(),
        users=UserRepository(session),
        user_daily_attempts=s.user_daily_attempts,
        daily_attempt_cap=s.daily_attempt_cap,
    )


def get_attempt_access(session: Session = Depends(get_session)):
    return AttemptAccessInteractor(
        attempts=AttemptRepository(session),
        loops=LoopRepository(session),
        nights=NightRepository(session),
        users=UserRepository(session),
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
        attempt_transaction=AttemptTransaction(session),
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
        night_transaction=NightTransaction(session),
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
        advisor_leads=bundle.advisor_leads,
        advisor_ladder=bundle.advisor_ladder,
        rule_templates=rule_templates(bundle),
        alternative_rank=get_alternative_rank(),
        night_transaction=NightTransaction(session),
    )


def rule_templates(bundle) -> list[dict]:
    """신의 개입 규칙 후보 — 원숭이손 소원 전용 행동(paw_only)은 플레이어 선택지에 올리지 않는다."""
    return [
        {"target": opportunity.actor, "when_beat": opportunity.beat, "effect": "enforce",
         "action": action, "label": f"{opportunity.actor}: {action}"}
        for opportunity in bundle.scene_actions if not opportunity.paw_only
        for action in ([EXPLAIN_ACTION, SOURCE_ACTION, opportunity.action]
                       if opportunity.known_source is not None else [EXPLAIN_ACTION, opportunity.action])
    ]


def get_inspector(session: Session = Depends(get_session)):
    return InspectorInteractor(
        attempts=AttemptRepository(session),
        rules=RuleRepository(session),
        event_log=EventLogRepository(session),
        inspector_token=get_settings().inspector_token,
        notes=NoteRepository(session),
        scenario=_scenario(),
    )


def get_auth_use_case(session: Session = Depends(get_session)) -> AuthUseCase:
    s = get_settings()
    dev = None
    if s.dev_login == "on" and s.dev_account_id and s.dev_account_password:
        dev = DevAccountDTO(account_id=s.dev_account_id, password=s.dev_account_password)
    return AuthInteractor(
        oauth=GoogleOAuthClient(
            client_id=s.google_oauth_client_id,
            client_secret=s.google_oauth_client_secret,
            redirect_uri=s.google_oauth_redirect_uri,
        ),
        users=UserRepository(session),
        tokens=SessionTokenSigner(s.session_secret),
        dev_account=dev,
    )


def get_health_use_case(session: Session = Depends(get_session)) -> HealthUseCase:
    def db_ping() -> bool:
        session.execute(text("SELECT 1"))
        return True

    return HealthInteractor(db_ping=db_ping)
