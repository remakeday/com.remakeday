"""시나리오 시드 테이블 4종 + 정답 주장 임베딩 테이블.

시드 참조 데이터라 라우터가 없다 (프랙탈 11-file set 예외, devlog 기록).
자연키 = (scenario, code류) 유니크 제약 → 매 기동 upsert의 기준.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.engine.app.ports.output.embedding_port import EMBEDDING_DIM
from core.matrix.grid_oracle_database_manager import Base


class ScenarioCharacterOrm(Base):
    __tablename__ = "scenario_characters"
    __table_args__ = (UniqueConstraint("scenario", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(64))
    persona: Mapped[str] = mapped_column(Text, default="")
    initial_suspicion: Mapped[int] = mapped_column(Integer, default=0)
    initial_trust: Mapped[int] = mapped_column(Integer, default=0)
    lost: Mapped[bool] = mapped_column(Boolean, default=False)


class ScenarioBeatOrm(Base):
    __tablename__ = "scenario_beats"
    __table_args__ = (UniqueConstraint("scenario", "n"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    n: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(128))
    narration: Mapped[str] = mapped_column(Text)
    morning_text: Mapped[str] = mapped_column(Text, default="")


class ScenarioTruthClaimOrm(Base):
    __tablename__ = "scenario_truth_claims"
    __table_args__ = (UniqueConstraint("scenario", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(32))
    cell: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)


class ScenarioCookieOrm(Base):
    __tablename__ = "scenario_cookies"
    __table_args__ = (UniqueConstraint("scenario", "text_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    text_id: Mapped[str] = mapped_column(String(32))
    cell: Mapped[str] = mapped_column(String(16))
    level: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class ScenarioFragmentOrm(Base):
    __tablename__ = "scenario_fragments"
    __table_args__ = (UniqueConstraint("scenario", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(32))  # fr-{loop}-{n}
    loop_n: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class TruthClaimEmbeddingOrm(Base):
    """정답 주장 임베딩 — 실제 채움은 P2 (시드 시 1회)."""

    __tablename__ = "truth_claim_embeddings"
    __table_args__ = (UniqueConstraint("scenario", "claim_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    claim_code: Mapped[str] = mapped_column(String(32))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
