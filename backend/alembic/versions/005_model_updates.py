"""model_updates table

Revision ID: 005
Revises: 004
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_updates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("model_version", sa.Integer(), nullable=False),
        sa.Column("threshold_suggestion", sa.Float(), nullable=False),
        sa.Column("federated_round", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("model_updates")
