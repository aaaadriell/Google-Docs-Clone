"""add now() default to users.created_at

Revision ID: 145c71767d5c
Revises: 06814c13b230
Create Date: 2026-10-13 12:56:07.261165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '145c71767d5c'
down_revision: Union[str, Sequence[str], None] = '06814c13b230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'created_at', server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'created_at', server_default=None)
