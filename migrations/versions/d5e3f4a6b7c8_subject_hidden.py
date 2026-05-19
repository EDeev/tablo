"""Add hidden flag to subject_configs

Revision ID: d5e3f4a6b7c8
Revises: c4d2e3f5a6b7
Create Date: 2026-05-04

"""
import sqlalchemy as sa
from alembic import op

revision = 'd5e3f4a6b7c8'
down_revision = 'c4d2e3f5a6b7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subject_configs') as batch_op:
        batch_op.add_column(
            sa.Column('hidden', sa.Boolean(), nullable=False, server_default='0')
        )


def downgrade():
    with op.batch_alter_table('subject_configs') as batch_op:
        batch_op.drop_column('hidden')
