"""Add household llm_settings JSONB column.

Revision ID: b2c4d6e8f0a1
Revises: 89c8afdcbbf5
Create Date: 2026-08-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, None] = "89c8afdcbbf5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "households",
        sa.Column(
            "llm_settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                "'{\"provider\": \"stub\", \"model\": \"stub-v1\", \"api_key_encrypted\": null}'::jsonb"
            ),
        ),
    )
    op.alter_column("households", "llm_settings", server_default=None)


def downgrade() -> None:
    op.drop_column("households", "llm_settings")
