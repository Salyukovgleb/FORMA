"""Add projects/members, preserving identity; nodes/main FK arrive in0004."""

import os

from alembic import op
import sqlalchemy as sa

revision = "0003_projects_access"
down_revision = "0002_sessions_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False, server_default=sa.text("''")),
        sa.Column("main_file_id", sa.Uuid()),
        sa.Column("engine", sa.Text(), nullable=False, server_default=sa.text("'xelatex'")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("revision", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("length(btrim(title))>0", name="ck_projects_title"),
        sa.CheckConstraint(
            "engine IN ('pdflatex','xelatex','lualatex')", name="ck_projects_engine"
        ),
        sa.CheckConstraint("status IN ('active','deleted')", name="ck_projects_status"),
        sa.CheckConstraint("revision>0", name="ck_projects_revision"),
        sa.CheckConstraint(
            "(status='deleted') = (deleted_at IS NOT NULL)", name="ck_projects_deleted"
        ),
        sa.CheckConstraint("main_file_id IS NULL", name="ck_projects_main_pending_nodes"),
    )
    op.create_index(
        "projects_owner", "projects", ["owner_id", sa.text("created_at DESC"), sa.text("id DESC")]
    )
    op.create_table(
        "project_members",
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "invited_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("role IN ('editor','viewer')", name="ck_project_members_role"),
    )
    op.create_index("project_members_user", "project_members", ["user_id", "project_id"])


def downgrade() -> None:
    name = op.get_bind().engine.url.database or ""
    if os.environ.get("FORMA_ALLOW_DESTRUCTIVE_DOWNGRADE") != "1" or not name.startswith(
        "forma_migration_test_"
    ):
        raise RuntimeError(
            "Destructive downgrade is allowed only in explicitly enabled disposable test databases"
        )
    op.drop_index("project_members_user", table_name="project_members")
    op.drop_table("project_members")
    op.drop_index("projects_owner", table_name="projects")
    op.drop_table("projects")
