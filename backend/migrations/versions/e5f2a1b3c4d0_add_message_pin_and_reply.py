"""add message pin and reply

Revision ID: e5f2a1b3c4d0
Revises: 28aed61d4c9f
Create Date: 2026-07-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

revision = 'e5f2a1b3c4d0'
down_revision = '28aed61d4c9f'
branch_labels = None
depends_on = None


def _column_exists(table, column):
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c['name'] for c in inspector.get_columns(table)]
    return column in cols


def upgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        if not _column_exists('messages', 'is_pinned'):
            batch_op.add_column(sa.Column('is_pinned', sa.Boolean(), nullable=True, server_default='0'))
        if not _column_exists('messages', 'reply_to_id'):
            batch_op.add_column(sa.Column('reply_to_id', sa.Integer(), nullable=True))
        if not _column_exists('messages', 'reply_to_content'):
            batch_op.add_column(sa.Column('reply_to_content', sa.Text(), nullable=True))
        if not _column_exists('messages', 'reply_to_sender'):
            batch_op.add_column(sa.Column('reply_to_sender', sa.String(100), nullable=True))


def downgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        for col in ['reply_to_sender', 'reply_to_content', 'reply_to_id', 'is_pinned']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
