"""npc_states.uttered_beat — 비트당 NPC 발화 1회 제한

Revision ID: a1b2c3d4e5f6
Revises: 9d274ffb88a1
Create Date: 2026-09-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9d274ffb88a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('npc_states', sa.Column('uttered_beat', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('npc_states', 'uttered_beat')
