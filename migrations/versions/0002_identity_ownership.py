"""identity ownership

Revision ID: 0002_identity_ownership
Revises: 0001_initial_schema
Create Date: 2026-05-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_identity_ownership"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return column_name in {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return index_name in {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _table_exists("tenants"):
        op.create_table(
            "tenants",
            sa.Column("tenant_id", sa.String(length=64), nullable=False),
            sa.Column("display_name", sa.String(length=128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("tenant_id"),
        )

    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("subject", sa.String(length=256), nullable=False),
            sa.Column("display_name", sa.String(length=128), nullable=False),
            sa.Column("token_fingerprint", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("user_id"),
            sa.UniqueConstraint("subject"),
        )

    if not _table_exists("tenant_memberships"):
        op.create_table(
            "tenant_memberships",
            sa.Column("tenant_id", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("tenant_id", "user_id"),
        )

    op.execute(
        """
        insert into tenants (tenant_id, display_name, created_at, updated_at)
        values ('tenant_default', 'Default Tenant', current_timestamp, current_timestamp)
        on conflict (tenant_id) do nothing
        """
    )
    op.execute(
        """
        insert into users (
            user_id,
            subject,
            display_name,
            token_fingerprint,
            created_at,
            updated_at
        ) values (
            'user_legacy',
            'legacy-backfill',
            'Legacy Backfill',
            null,
            current_timestamp,
            current_timestamp
        )
        on conflict (user_id) do nothing
        """
    )
    op.execute(
        """
        insert into tenant_memberships (
            tenant_id,
            user_id,
            role,
            created_at,
            updated_at
        ) values (
            'tenant_default',
            'user_legacy',
            'admin',
            current_timestamp,
            current_timestamp
        )
        on conflict (tenant_id, user_id) do nothing
        """
    )

    with op.batch_alter_table("run_states") as batch_op:
        if not _column_exists("run_states", "tenant_id"):
            batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=True))
        if not _column_exists("run_states", "owner_user_id"):
            batch_op.add_column(sa.Column("owner_user_id", sa.String(length=64), nullable=True))
        if not _column_exists("run_states", "created_by_user_id"):
            batch_op.add_column(
                sa.Column("created_by_user_id", sa.String(length=64), nullable=True)
            )

    op.execute(
        """
        update run_states
        set tenant_id = 'tenant_default',
            owner_user_id = 'user_legacy',
            created_by_user_id = 'user_legacy'
        where tenant_id is null
        """
    )

    with op.batch_alter_table("run_states") as batch_op:
        batch_op.alter_column(
            "tenant_id",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        batch_op.alter_column(
            "owner_user_id",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        batch_op.alter_column(
            "created_by_user_id",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_run_states_tenant",
            "tenants",
            ["tenant_id"],
            ["tenant_id"],
        )
        batch_op.create_foreign_key(
            "fk_run_states_owner_user",
            "users",
            ["owner_user_id"],
            ["user_id"],
        )
        batch_op.create_foreign_key(
            "fk_run_states_created_by_user",
            "users",
            ["created_by_user_id"],
            ["user_id"],
        )

    _create_index_if_missing("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"])
    _create_index_if_missing("ix_users_token_fingerprint", "users", ["token_fingerprint"])
    _create_index_if_missing("ix_run_states_tenant_id", "run_states", ["tenant_id"])
    _create_index_if_missing("ix_run_states_owner_user_id", "run_states", ["owner_user_id"])
    _create_index_if_missing("ix_run_states_tenant_status", "run_states", ["tenant_id", "status"])
    _create_index_if_missing(
        "ix_run_states_tenant_workflow_type",
        "run_states",
        ["tenant_id", "workflow_type"],
    )


def downgrade() -> None:
    _drop_index_if_exists("ix_run_states_tenant_workflow_type", "run_states")
    _drop_index_if_exists("ix_run_states_tenant_status", "run_states")
    _drop_index_if_exists("ix_run_states_owner_user_id", "run_states")
    _drop_index_if_exists("ix_run_states_tenant_id", "run_states")
    _drop_index_if_exists("ix_users_token_fingerprint", "users")
    _drop_index_if_exists("ix_tenant_memberships_user_id", "tenant_memberships")

    with op.batch_alter_table("run_states") as batch_op:
        batch_op.drop_constraint("fk_run_states_created_by_user", type_="foreignkey")
        batch_op.drop_constraint("fk_run_states_owner_user", type_="foreignkey")
        batch_op.drop_constraint("fk_run_states_tenant", type_="foreignkey")
        batch_op.drop_column("created_by_user_id")
        batch_op.drop_column("owner_user_id")
        batch_op.drop_column("tenant_id")

    if _table_exists("tenant_memberships"):
        op.drop_table("tenant_memberships")
    if _table_exists("users"):
        op.drop_table("users")
    if _table_exists("tenants"):
        op.drop_table("tenants")
