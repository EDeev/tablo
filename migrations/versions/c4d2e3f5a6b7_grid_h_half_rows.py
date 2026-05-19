"""grid_h in half-row units (1=0.5row, 2=1row, 4=2rows)

Revision ID: c4d2e3f5a6b7
Revises: b3c9d1e2f4a5
Create Date: 2026-05-03

"""
from alembic import op

revision = 'c4d2e3f5a6b7'
down_revision = 'b3c9d1e2f4a5'
branch_labels = None
depends_on = None


def upgrade():
    # Старые записи: grid_h=1 означало «1 строка» → теперь «2 полустроки»
    op.execute("UPDATE metrics SET grid_h = grid_h * 2")


def downgrade():
    op.execute("UPDATE metrics SET grid_h = GREATEST(grid_h / 2, 1)")
