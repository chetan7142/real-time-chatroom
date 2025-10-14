"""Add new tables and update existing ones

Revision ID: 7aa453b3e59c
Revises: 0003_create_messages
Create Date: 2025-10-15 00:18:37.892745

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7aa453b3e59c'
down_revision = '0003_create_messages'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('profile_pic', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=20), nullable=True, default='offline'))
    op.add_column('users', sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True))
    
    # Add new columns to rooms table
    op.add_column('rooms', sa.Column('description', sa.Text(), nullable=True))
    
    # Create room_members table
    op.create_table('room_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('MEMBER', 'ADMIN', 'OWNER', name='roomrole'), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_room_members_id'), 'room_members', ['id'], unique=False)
    
    # Create files table
    op.create_table('files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.String(length=500), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    
    # Create mentions table
    op.create_table('mentions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('mentioned_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentioned_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mentions_id'), 'mentions', ['id'], unique=False)


def downgrade():
    # Drop new tables
    op.drop_table('mentions')
    op.drop_table('notifications')
    op.drop_table('files')
    op.drop_table('room_members')
    
    # Remove new columns from rooms table
    op.drop_column('rooms', 'description')
    
    # Remove new columns from users table
    op.drop_column('users', 'last_seen')
    op.drop_column('users', 'status')
    op.drop_column('users', 'profile_pic')
    
    # Drop enum type
    op.execute('DROP TYPE roomrole')
