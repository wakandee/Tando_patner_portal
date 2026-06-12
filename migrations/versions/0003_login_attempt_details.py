"""login attempt details

Revision ID: 0003_login_attempt_details
Revises: 0002_login_attempts_audit
Create Date: 2026-06-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0003_login_attempt_details"
down_revision = "0002_login_attempts_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("login_attempt", sa.Column("browser", sa.String(length=120), nullable=True))
    op.add_column("login_attempt", sa.Column("device_type", sa.String(length=80), nullable=True))


def downgrade():
    op.drop_column("login_attempt", "device_type")
    op.drop_column("login_attempt", "browser")
