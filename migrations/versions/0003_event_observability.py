"""event observability metadata

Revision ID: 0003_event_observability
Revises: 0002_identity_ownership
Create Date: 2026-05-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_event_observability"
down_revision: str | None = "0002_identity_ownership"
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
    with op.batch_alter_table("run_events") as batch_op:
        if not _column_exists("run_events", "request_id"):
            batch_op.add_column(
                sa.Column(
                    "request_id",
                    sa.String(length=96),
                    nullable=False,
                    server_default="",
                )
            )
        if not _column_exists("run_events", "traceparent"):
            batch_op.add_column(
                sa.Column(
                    "traceparent",
                    sa.String(length=128),
                    nullable=False,
                    server_default="",
                )
            )

    _create_index_if_missing("ix_run_events_request_id", "run_events", ["request_id"])
    _create_index_if_missing("ix_run_events_traceparent", "run_events", ["traceparent"])


def downgrade() -> None:
    _drop_index_if_exists("ix_run_events_traceparent", "run_events")
    _drop_index_if_exists("ix_run_events_request_id", "run_events")
    with op.batch_alter_table("run_events") as batch_op:
        batch_op.drop_column("traceparent")
        batch_op.drop_column("request_id")
