"""Create rooms table"""

from alembic import op
import sqlalchemy as sa

revision = '0002_create_rooms'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False, default=False),
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('rooms')
