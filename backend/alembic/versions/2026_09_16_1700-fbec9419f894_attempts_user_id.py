"""attempts_user_id

과잉 사용 방지 허들 — attempts를 user_id로 집계해 로그인 사용자별 일일 판 수를
셀 수 있게 한다 (익명 판은 user_id NULL로 유지, 하위 호환).

Revision ID: fbec9419f894
Revises: 64a6b77faeb0
Create Date: 2026-09-16 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fbec9419f894'
down_revision: Union[str, None] = '64a6b77faeb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_attempts_user_id", table_name="attempts")
    op.drop_column("attempts", "user_id")
