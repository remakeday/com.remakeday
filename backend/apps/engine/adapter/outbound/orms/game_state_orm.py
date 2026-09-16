"""게임 상태 테이블 — 명시적 상태 (이벤트 소싱 아님, P1 설계 결정 4)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.matrix.grid_oracle_database_manager import Base


class AttemptOrm(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_n: Mapped[int] = mapped_column(Integer, default=1)
    prior_attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|closed
    closed_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prior_cell_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cookies_seen: Mapped[list] = mapped_column(JSONB, default=list)
    paw_offered_count: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LoopOrm(Base):
    __tablename__ = "loops"
    __table_args__ = (UniqueConstraint("attempt_id", "loop_n"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id"))
    loop_n: Mapped[int] = mapped_column(Integer)
    beat: Mapped[int] = mapped_column(Integer, default=1)
    budget_left: Mapped[int] = mapped_column(Integer)
    ask_budget_left: Mapped[int] = mapped_column(Integer, default=2)
    manager_budget_left: Mapped[int] = mapped_column(Integer, default=2)
    state: Mapped[str] = mapped_column(String(20), default="day")
    # day | night_pending | night_draft | scored | intervention | closed
    damage_level: Mapped[int] = mapped_column(Integer, default=0)
    morning_shifted: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    world_outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)
    anomaly_count: Mapped[int] = mapped_column(Integer, default=0)
    rumor_index: Mapped[int] = mapped_column(Integer, default=0)
    cause_chain: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    side_effect_claims: Mapped[list] = mapped_column(JSONB, default=list)
    pending_paw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class NpcStateOrm(Base):
    __tablename__ = "npc_states"
    __table_args__ = (UniqueConstraint("loop_id", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loops.id"))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    suspicion: Mapped[int] = mapped_column(Integer, default=0)
    trust: Mapped[int] = mapped_column(Integer, default=0)
    opposite_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    flagged_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    mood: Mapped[str] = mapped_column(String(16), default="calm")
    uttered_beat: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 이 비트에 말 걸었으면 그 비트 번호
    memory: Mapped[list] = mapped_column(JSONB, default=list)  # Source-addressed day memories; legacy strings readable.
    plan: Mapped[list | None] = mapped_column(JSONB, nullable=True)


class NoteOrm(Base):
    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("attempt_id", "source_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id"))
    kind: Mapped[str] = mapped_column(String(20))  # fragment|confirmed|rule_observation|advice
    text: Mapped[str] = mapped_column(Text)
    loop_n: Mapped[int] = mapped_column(Integer)
    source_key: Mapped[str] = mapped_column(String(255))


class RuleOrm(Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("attempt_id", "rule_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id"))
    rule_id: Mapped[str] = mapped_column(String(8))  # R1, R2...
    source: Mapped[str] = mapped_column(String(16))
    target: Mapped[str] = mapped_column(String(64))
    when_beat: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null=any
    effect: Mapped[str] = mapped_column(String(10))
    action: Mapped[str] = mapped_column(String(64))
    shown_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    hidden_side_effect: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_loop: Mapped[int] = mapped_column(Integer)
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)


class NightOrm(Base):
    __tablename__ = "nights"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    loop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loops.id"), unique=True)
    tapped_note_ids: Mapped[list] = mapped_column(JSONB, default=list)
    free_text: Mapped[str] = mapped_column(Text, default="")
    claims: Mapped[list] = mapped_column(JSONB, default=list)
    fabricated_dropped: Mapped[list] = mapped_column(JSONB, default=list)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edit_count: Mapped[int] = mapped_column(Integer, default=0)
    submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    per_truth_claim: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    cell_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    questions_left: Mapped[int] = mapped_column(Integer, default=3)
    questions: Mapped[list] = mapped_column(JSONB, default=list)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    rule_chosen: Mapped[bool] = mapped_column(Boolean, default=False)
