"""add grid layout to metrics

Revision ID: b3c9d1e2f4a5
Revises: aa6f28d23573
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa

revision = 'b3c9d1e2f4a5'
down_revision = 'aa6f28d23573'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('metrics') as batch_op:
        batch_op.add_column(sa.Column('grid_col', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('grid_row', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('grid_w',   sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('grid_h',   sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    with op.batch_alter_table('metrics') as batch_op:
        batch_op.drop_column('grid_h')
        batch_op.drop_column('grid_w')
        batch_op.drop_column('grid_row')
        batch_op.drop_column('grid_col')
