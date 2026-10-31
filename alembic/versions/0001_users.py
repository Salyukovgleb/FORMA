"""Create accounts without implementing identity API."""

import os

from alembic import op
import sqlalchemy as sa

revision = "0001_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("email = lower(btrim(email))", name="ck_users_email_normalized"),
        sa.CheckConstraint("length(display_name)>0", name="ck_users_display_name"),
    )


def downgrade() -> None:
    name = op.get_bind().engine.url.database or ""
    if os.environ.get("FORMA_ALLOW_DESTRUCTIVE_DOWNGRADE") != "1" or not name.startswith(
        "forma_migration_test_"
    ):
        raise RuntimeError(
            "Destructive downgrade is allowed only in explicitly enabled disposable test databases"
        )
    op.drop_table("users")
