"""compatibility shim for missing migration

Revision ID: c9374e10f09e
Revises: 0001_initial_schema
Create Date: 2026-06-12 00:00:00.000000

This migration restores a missing revision identifier referenced by
existing databases so Alembic can continue upgrading the chain.
"""

from alembic import op


revision = "c9374e10f09e"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
