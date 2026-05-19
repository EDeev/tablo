"""Add completion_type, completed, sdo_url to subject_configs; ai_prompt to metrics

Revision ID: e6f4a5b8c9d0
Revises: d5e3f4a6b7c8
Create Date: 2026-05-11

"""
import sqlalchemy as sa
from alembic import op

revision = 'e6f4a5b8c9d0'
down_revision = 'd5e3f4a6b7c8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subject_configs') as batch_op:
        batch_op.add_column(
            sa.Column('completion_type', sa.String(32), nullable=True)
        )
        batch_op.add_column(
            sa.Column('completed', sa.Boolean(), nullable=False, server_default='0')
        )
        batch_op.add_column(
            sa.Column('sdo_url', sa.Text(), nullable=True)
        )
    with op.batch_alter_table('metrics') as batch_op:
        batch_op.add_column(
            sa.Column('ai_prompt', sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('subject_configs') as batch_op:
        batch_op.drop_column('sdo_url')
        batch_op.drop_column('completed')
        batch_op.drop_column('completion_type')
    with op.batch_alter_table('metrics') as batch_op:
        batch_op.drop_column('ai_prompt')
