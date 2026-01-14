"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("file_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "template_cells",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("sheet_name", sa.String(length=255), nullable=False, server_default="Sheet1"),
        sa.Column("cell_ref", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("data_type", sa.String(length=50), nullable=False, server_default="text"),
        sa.UniqueConstraint("template_id","sheet_name","cell_ref", name="uq_template_cell"),
    )
    op.create_index("ix_template_cells_template_id", "template_cells", ["template_id"])

    op.create_table(
        "instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
    )
    op.create_index("ix_instances_template_id", "instances", ["template_id"])

    op.create_table(
        "instance_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("instances.id"), nullable=False),
        sa.Column("sheet_name", sa.String(length=255), nullable=False),
        sa.Column("cell_ref", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.UniqueConstraint("instance_id","sheet_name","cell_ref", name="uq_instance_value"),
    )
    op.create_index("ix_instance_values_instance_id", "instance_values", ["instance_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("instances.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("sheet_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("cell_ref", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("old_value", sa.Text(), nullable=False, server_default=""),
        sa.Column("new_value", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("meta_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_events_instance_id", "audit_events", ["instance_id"])

def downgrade():
    op.drop_index("ix_audit_events_instance_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_instance_values_instance_id", table_name="instance_values")
    op.drop_table("instance_values")
    op.drop_index("ix_instances_template_id", table_name="instances")
    op.drop_table("instances")
    op.drop_index("ix_template_cells_template_id", table_name="template_cells")
    op.drop_table("template_cells")
    op.drop_table("templates")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
