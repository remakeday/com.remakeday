"""survey_votes

클리어 화면 플레이 평가 — 판당 한 표(유니크), 항목별 1~5점 부분 응답 허용,
건너뛰기도 행으로 남긴다. 기존 테이블은 건드리지 않는다.

Revision ID: 216f290d03b3
Revises: fbec9419f894
Create Date: 2026-09-19 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '216f290d03b3'
down_revision: Union[str, None] = 'fbec9419f894'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCORES = ("fun", "novelty", "ai_agency", "polish", "recommend")
_FILLED = "num_nonnulls(" + ", ".join(_SCORES) + ")"


def upgrade() -> None:
    op.create_table(
        "survey_votes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("skipped", sa.Boolean(), nullable=False, server_default=sa.false()),
        *(sa.Column(name, sa.SmallInteger(), nullable=True) for name in _SCORES),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("attempt_id", name="uq_survey_votes_attempt"),
        *(
            sa.CheckConstraint(
                f"{name} IS NULL OR ({name} BETWEEN 1 AND 5)", name=f"ck_survey_votes_{name}"
            )
            for name in _SCORES
        ),
        sa.CheckConstraint(
            f"(skipped AND {_FILLED} = 0) OR (NOT skipped AND {_FILLED} > 0)",
            name="ck_survey_votes_skip_consistency",
        ),
    )
    op.create_index("ix_survey_votes_user_id", "survey_votes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_survey_votes_user_id", table_name="survey_votes")
    op.drop_table("survey_votes")
