"""Reconcile ORM schema drift

Revision ID: 009
Revises: 008
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _columns(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def _create_index_once(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if index_name not in _indexes(table_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _ensure_agent_analyses() -> None:
    if _table_exists("agent_analysis") and not _table_exists("agent_analyses"):
        op.rename_table("agent_analysis", "agent_analyses")

    if not _table_exists("agent_analyses"):
        op.create_table(
            "agent_analyses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("crop", sa.String(), nullable=False),
            sa.Column("city", sa.String(), nullable=False),
            sa.Column("current_price", sa.Float(), nullable=False),
            sa.Column("predicted_price", sa.Float(), nullable=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("best_action_date", sa.String(), nullable=True),
            sa.Column("expected_price", sa.Float(), nullable=True),
            sa.Column("risk_level", sa.String(), nullable=False),
            sa.Column("market_signals", sa.JSON(), nullable=True),
            sa.Column("llm_insights", sa.Text(), nullable=True),
            sa.Column("analysis_duration", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        )
    else:
        columns = _columns("agent_analyses")

        with op.batch_alter_table("agent_analyses") as batch_op:
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            if "action" not in columns and "decision_action" in columns:
                batch_op.alter_column("decision_action", new_column_name="action")
            elif "action" not in columns:
                batch_op.add_column(sa.Column("action", sa.String(), nullable=True))
            if "reason" not in columns and "reasoning" in columns:
                batch_op.alter_column("reasoning", new_column_name="reason")
            elif "reason" not in columns:
                batch_op.add_column(sa.Column("reason", sa.Text(), nullable=True))
            if "best_action_date" not in columns:
                batch_op.add_column(sa.Column("best_action_date", sa.String(), nullable=True))
            if "expected_price" not in columns:
                batch_op.add_column(sa.Column("expected_price", sa.Float(), nullable=True))
            if "analysis_duration" not in columns:
                batch_op.add_column(sa.Column("analysis_duration", sa.Float(), nullable=True))

        if "user_id" not in columns:
            try:
                with op.batch_alter_table("agent_analyses") as batch_op:
                    batch_op.create_foreign_key(
                        "fk_agent_analyses_user_id_users",
                        "users",
                        ["user_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
            except NotImplementedError:
                pass

        if "confidence" in _columns("agent_analyses") and op.get_bind().dialect.name != "sqlite":
            op.alter_column("agent_analyses", "confidence", type_=sa.Float())

    _create_index_once("ix_agent_analyses_id", "agent_analyses", ["id"])
    _create_index_once("ix_agent_analyses_user_id", "agent_analyses", ["user_id"])
    _create_index_once("ix_agent_analyses_crop", "agent_analyses", ["crop"])
    _create_index_once("ix_agent_analyses_created_at", "agent_analyses", ["created_at"])


def _ensure_prediction_history() -> None:
    if not _table_exists("prediction_history"):
        op.create_table(
            "prediction_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("prediction_type", sa.String(), nullable=False),
            sa.Column("crop", sa.String(), nullable=False),
            sa.Column("input_parameters", sa.JSON(), nullable=False),
            sa.Column("prediction_result", sa.JSON(), nullable=False),
            sa.Column("user_ip", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        )
    else:
        columns = _columns("prediction_history")
        with op.batch_alter_table("prediction_history") as batch_op:
            if "prediction_type" not in columns:
                batch_op.add_column(sa.Column("prediction_type", sa.String(), nullable=True))
            if "input_parameters" not in columns:
                batch_op.add_column(sa.Column("input_parameters", sa.JSON(), nullable=True))
            if "prediction_result" not in columns:
                batch_op.add_column(sa.Column("prediction_result", sa.JSON(), nullable=True))
            if "user_ip" not in columns:
                batch_op.add_column(sa.Column("user_ip", sa.String(), nullable=True))

        op.execute("UPDATE prediction_history SET prediction_type = 'price' WHERE prediction_type IS NULL")
        op.execute("UPDATE prediction_history SET input_parameters = '{}' WHERE input_parameters IS NULL")
        op.execute("UPDATE prediction_history SET prediction_result = '{}' WHERE prediction_result IS NULL")

        if op.get_bind().dialect.name != "sqlite":
            op.alter_column("prediction_history", "prediction_type", nullable=False)
            op.alter_column("prediction_history", "input_parameters", nullable=False)
            op.alter_column("prediction_history", "prediction_result", nullable=False)

    _create_index_once("ix_prediction_history_id", "prediction_history", ["id"])
    _create_index_once("ix_prediction_history_crop", "prediction_history", ["crop"])
    _create_index_once("ix_prediction_history_created_at", "prediction_history", ["created_at"])


def _ensure_user_float_columns() -> None:
    if not _table_exists("users") or op.get_bind().dialect.name == "sqlite":
        return

    op.alter_column("users", "farm_size", type_=sa.Float())
    op.alter_column("users", "farm_location_lat", type_=sa.Float())
    op.alter_column("users", "farm_location_lon", type_=sa.Float())


def upgrade() -> None:
    _ensure_agent_analyses()
    _ensure_prediction_history()
    _ensure_user_float_columns()


def downgrade() -> None:
    # This migration intentionally preserves reconciled data. Reversing it would
    # require dropping live columns or renaming tables back to obsolete names.
    pass
