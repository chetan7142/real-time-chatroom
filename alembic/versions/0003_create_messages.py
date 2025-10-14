"""Create messages table"""

from alembic import op
import sqlalchemy as sa

revision = '0003_create_messages'
down_revision = '0002_create_rooms'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('room_id', sa.Integer, sa.ForeignKey('rooms.id', ondelete='CASCADE')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False)
    )

def downgrade():
    op.drop_table('messages')
