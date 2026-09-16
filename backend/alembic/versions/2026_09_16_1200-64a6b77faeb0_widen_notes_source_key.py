"""widen_notes_source_key

notes.source_key was VARCHAR(64), but a "confirmed" note's source_key is built
from the full observation_id (f"confirmed-{loop.id}:{key}") which routinely
exceeds 64 characters for real scenario action keys, causing a DataError on
insert (F7 신의 질문 — Task 5).

Revision ID: 64a6b77faeb0
Revises: a8b1ba0fa71f
Create Date: 2026-09-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '64a6b77faeb0'
down_revision: Union[str, None] = 'a8b1ba0fa71f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('notes', 'source_key', existing_type=sa.String(length=64),
                     type_=sa.String(length=255), existing_nullable=False)


def downgrade() -> None:
    op.alter_column('notes', 'source_key', existing_type=sa.String(length=255),
                     type_=sa.String(length=64), existing_nullable=False)
