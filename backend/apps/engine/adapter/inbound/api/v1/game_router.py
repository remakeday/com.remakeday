"""게임 API — 계약: docs/spec/api_contract.md."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints

from apps.engine.adapter.inbound.api.v1.guards import client_ip, ip_bucket, ip_hash, require_user
from apps.engine.app.use_cases.intervention_interactor import (
    GameStateError as InterventionError,
)
from apps.engine.app.use_cases.inspector_interactor import AccessDenied
from apps.engine.app.use_cases.loop_interactor import GameStateError as LoopError
from apps.engine.app.use_cases.loop_interactor import DialogueUnavailable
from apps.engine.app.use_cases.night_interactor import GameStateError as NightError
from apps.engine.app.use_cases.session_interactor import DailyCapReached, UserDailyLimit
from apps.engine.dependencies.engine_dependency import (
    get_inspector,
    get_intervention_interactor,
    get_loop_interactor,
    get_night_interactor,
    get_session_interactor,
)

router = APIRouter(tags=["game"])

_STATE_ERRORS = (LoopError, NightError, InterventionError)


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except _STATE_ERRORS as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except AccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except DialogueUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except UserDailyLimit:
        return JSONResponse(
            status_code=403,
            content={"code": "daily_attempt_limit", "detail": "오늘은 여기까지. 내일 다시 시작할 수 있다."},
        )
    except DailyCapReached:
        return JSONResponse(
            status_code=503,
            content={"code": "daily_cap", "detail": "오늘 정원이 마감됐다."},
        )


class SessionReq(BaseModel):
    prior_attempt_id: str | None = None


class UtteranceReq(BaseModel):
    target: str
    text: str = Field(max_length=200)
    request_id: uuid.UUID | None = None


class PawReq(BaseModel):
    offer_id: str
    accept: bool


class DraftReq(BaseModel):
    tapped_note_ids: list[int] = []
    free_text: str = Field("", max_length=2000)
    inherited_note_ids: list[int] = []


class ClaimsReq(BaseModel):
    claims: list[Annotated[str, StringConstraints(max_length=500)]] = Field(max_length=8)


class QuestionReq(BaseModel):
    text: str = Field(max_length=200)


class RuleReq(BaseModel):
    choice: str  # "1"|"2"|"3"|"custom"
    custom_text: str | None = Field(None, max_length=200)
    preview_id: str | None = None


class RulePreviewReq(BaseModel):
    custom_text: str = Field(max_length=200)


@router.post("/sessions", dependencies=[Depends(ip_bucket("sessions", "ip_sessions_per_minute"))])
def create_session(req: SessionReq, request: Request, user=Depends(require_user), uc=Depends(get_session_interactor)):
    prior = uuid.UUID(req.prior_attempt_id) if req.prior_attempt_id else None
    return _run(uc.start, prior, user, ip_hash(client_ip(request)))


@router.post("/sessions/{attempt_id}/loops")
def start_loop(attempt_id: uuid.UUID, user=Depends(require_user), uc=Depends(get_loop_interactor)):
    return _run(uc.start_loop, attempt_id)


@router.post("/loops/{loop_id}/utterances", dependencies=[Depends(ip_bucket("actions", "ip_actions_per_minute"))])
def utter(loop_id: uuid.UUID, req: UtteranceReq, user=Depends(require_user), uc=Depends(get_loop_interactor)):
    return _run(uc.utter, loop_id, req.target, req.text, request_id=req.request_id)


@router.post("/loops/{loop_id}/beats/next")
def next_beat(loop_id: uuid.UUID, user=Depends(require_user), uc=Depends(get_loop_interactor)):
    return _run(uc.advance_beat, loop_id)


@router.post("/loops/{loop_id}/paw/respond")
def respond_paw(loop_id: uuid.UUID, req: PawReq, user=Depends(require_user), uc=Depends(get_loop_interactor)):
    return _run(uc.respond_paw, loop_id, req.offer_id, req.accept)


@router.get("/loops/{loop_id}/notes")
def notes(loop_id: uuid.UUID, uc=Depends(get_loop_interactor)):
    return _run(uc.list_notes, loop_id)


@router.get("/loops/{loop_id}/observations")
def observations(loop_id: uuid.UUID, uc=Depends(get_loop_interactor)):
    return _run(uc.list_observations, loop_id)


@router.get("/loops/{loop_id}/night/previous")
def previous_answer(loop_id: uuid.UUID, uc=Depends(get_night_interactor)):
    return _run(uc.previous_answer, loop_id)


@router.get("/loops/{loop_id}/npcs")
def npcs(loop_id: uuid.UUID, uc=Depends(get_loop_interactor)):
    return _run(uc.list_npcs, loop_id)


@router.post("/loops/{loop_id}/night/draft")
def night_draft(loop_id: uuid.UUID, req: DraftReq, user=Depends(require_user), uc=Depends(get_night_interactor)):
    return _run(uc.draft, loop_id, req.tapped_note_ids, req.free_text, req.inherited_note_ids)


@router.patch("/nights/{night_id}/claims")
def edit_claims(night_id: uuid.UUID, req: ClaimsReq, user=Depends(require_user), uc=Depends(get_night_interactor)):
    return _run(uc.edit_claims, night_id, req.claims)


@router.post("/nights/{night_id}/submit")
def submit(night_id: uuid.UUID, user=Depends(require_user), uc=Depends(get_night_interactor)):
    return _run(uc.submit, night_id)


@router.post("/nights/{night_id}/questions", dependencies=[Depends(ip_bucket("actions", "ip_actions_per_minute"))])
def ask_question(night_id: uuid.UUID, req: QuestionReq, user=Depends(require_user), uc=Depends(get_intervention_interactor)):
    return _run(uc.ask, night_id, req.text)


@router.get("/nights/{night_id}/options")
def options(night_id: uuid.UUID, uc=Depends(get_intervention_interactor)):
    return _run(uc.options, night_id)


@router.post("/nights/{night_id}/rule")
def choose_rule(night_id: uuid.UUID, req: RuleReq, user=Depends(require_user), uc=Depends(get_intervention_interactor)):
    return _run(uc.choose_rule, night_id, req.choice, req.custom_text, req.preview_id)


@router.post("/nights/{night_id}/rule/preview")
def preview_rule(night_id: uuid.UUID, req: RulePreviewReq, user=Depends(require_user), uc=Depends(get_intervention_interactor)):
    return _run(uc.preview_rule, night_id, req.custom_text)


@router.get("/attempts/{attempt_id}/journey")
def journey(attempt_id: uuid.UUID, uc=Depends(get_inspector)):
    return _run(uc.journey_view, attempt_id)


@router.get("/attempts/{attempt_id}/harness")
def harness(attempt_id: uuid.UUID, uc=Depends(get_inspector)):
    return _run(uc.harness_view, attempt_id)


@router.get("/attempts/{attempt_id}/inspector")
def inspector(attempt_id: uuid.UUID, token: str = "", uc=Depends(get_inspector)):
    return _run(uc.inspector_view, attempt_id, token)
