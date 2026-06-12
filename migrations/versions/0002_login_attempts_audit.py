"""login attempts audit

Revision ID: 0002_login_attempts_audit
Revises: c9374e10f09e
Create Date: 2026-06-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_login_attempts_audit"
down_revision = "c9374e10f09e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "login_attempt",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failure_reason", sa.String(length=120), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index(op.f("ix_login_attempt_email"), "login_attempt", ["email"], unique=False)
    op.create_index(op.f("ix_login_attempt_user_id"), "login_attempt", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_login_attempt_user_id"), table_name="login_attempt")
    op.drop_index(op.f("ix_login_attempt_email"), table_name="login_attempt")
    op.drop_table("login_attempt")
