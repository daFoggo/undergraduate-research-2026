"""Create research dataset import registry.

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS research")
    op.create_table(
        "dataset_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("issue_count", sa.BigInteger(), nullable=True),
        sa.Column("project_count", sa.Integer(), nullable=True),
        sa.Column("sprint_count", sa.Integer(), nullable=True),
        schema="research",
    )


def downgrade() -> None:
    op.drop_table("dataset_imports", schema="research")
    op.execute("DROP SCHEMA IF EXISTS research")

