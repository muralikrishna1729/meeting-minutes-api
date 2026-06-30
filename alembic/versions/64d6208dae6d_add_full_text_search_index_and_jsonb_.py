"""add full text search index and jsonb cast

Revision ID: 64d6208dae6d
Revises: d394ddde3458
Create Date: 2026-06-30 04:35:08.404742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64d6208dae6d'
down_revision: Union[str, Sequence[str], None] = 'd394ddde3458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE meeting_minutes
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(original_text, '') || ' ' || coalesce(summary, ''))
        ) STORED;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_meeting_minutes_search_vector
        ON meeting_minutes USING GIN(search_vector);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_meeting_minutes_search_vector;")
    op.execute("ALTER TABLE meeting_minutes DROP COLUMN IF EXISTS search_vector;")
