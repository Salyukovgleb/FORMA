"""Add session rotation and rate-limit storage without changing existing accounts."""

import os

from alembic import op
import sqlalchemy as sa

revision = "0002_sessions_limits"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("refresh_token_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("csrf_token_hash", sa.CHAR(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "rotated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
    )
    op.create_index("auth_sessions_user", "auth_sessions", ["user_id", "expires_at"])
    op.create_table(
        "used_refresh_tokens",
        sa.Column("token_hash", sa.CHAR(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("auth_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "rate_limit_buckets",
        sa.Column("scope", sa.String(80), primary_key=True),
        sa.Column("subject_hash", sa.CHAR(64), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count>=0", name="ck_rate_count"),
    )


def downgrade() -> None:
    name = op.get_bind().engine.url.database or ""
    if os.environ.get("FORMA_ALLOW_DESTRUCTIVE_DOWNGRADE") != "1" or not name.startswith(
        "forma_migration_test_"
    ):
        raise RuntimeError(
            "Destructive downgrade is allowed only in explicitly enabled disposable test databases"
        )
    op.drop_table("rate_limit_buckets")
    op.drop_table("used_refresh_tokens")
    op.drop_index("auth_sessions_user", table_name="auth_sessions")
    op.drop_table("auth_sessions")
