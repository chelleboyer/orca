"""add_relationship_tables

Revision ID: c9b2f8a4d5e6
Revises: e4392fd7a1cb
Create Date: 2025-09-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c9b2f8a4d5e6'
down_revision = 'e4392fd7a1cb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cardinality type enum
    cardinality_enum = postgresql.ENUM('1:1', '1:N', 'N:M', name='cardinalitytype')
    cardinality_enum.create(op.get_bind())
    
    # Create relationships table
    op.create_table('relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_object_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_object_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cardinality', cardinality_enum, nullable=False),
        sa.Column('forward_label', sa.String(), nullable=True),
        sa.Column('reverse_label', sa.String(), nullable=True),
        sa.Column('is_bidirectional', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strength', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_object_id'], ['objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_object_id'], ['objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_object_id', 'target_object_id', name='uq_relationship_objects')
    )
    op.create_index(op.f('ix_relationships_project_id'), 'relationships', ['project_id'], unique=False)
    op.create_index(op.f('ix_relationships_source_object_id'), 'relationships', ['source_object_id'], unique=False)
    op.create_index(op.f('ix_relationships_target_object_id'), 'relationships', ['target_object_id'], unique=False)
    
    # Create relationship_locks table
    op.create_table('relationship_locks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_object_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_object_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('locked_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('locked_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('lock_type', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['locked_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_object_id'], ['objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_object_id'], ['objects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_object_id', 'target_object_id', name='uq_lock_objects')
    )
    op.create_index(op.f('ix_relationship_locks_expires_at'), 'relationship_locks', ['expires_at'], unique=False)
    op.create_index(op.f('ix_relationship_locks_locked_by'), 'relationship_locks', ['locked_by'], unique=False)
    
    # Create user_presence table
    op.create_table('user_presence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('current_object_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_activity', sa.String(length=100), nullable=True),
        sa.Column('matrix_row', sa.Integer(), nullable=True),
        sa.Column('matrix_col', sa.Integer(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['current_object_id'], ['objects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_presence_project_user')
    )
    op.create_index(op.f('ix_user_presence_last_seen'), 'user_presence', ['last_seen'], unique=False)
    op.create_index(op.f('ix_user_presence_project_id'), 'user_presence', ['project_id'], unique=False)
    op.create_index(op.f('ix_user_presence_user_id'), 'user_presence', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_presence_user_id'), table_name='user_presence')
    op.drop_index(op.f('ix_user_presence_project_id'), table_name='user_presence')
    op.drop_index(op.f('ix_user_presence_last_seen'), table_name='user_presence')
    op.drop_table('user_presence')
    
    op.drop_index(op.f('ix_relationship_locks_locked_by'), table_name='relationship_locks')
    op.drop_index(op.f('ix_relationship_locks_expires_at'), table_name='relationship_locks')
    op.drop_table('relationship_locks')
    
    op.drop_index(op.f('ix_relationships_target_object_id'), table_name='relationships')
    op.drop_index(op.f('ix_relationships_source_object_id'), table_name='relationships')
    op.drop_index(op.f('ix_relationships_project_id'), table_name='relationships')
    op.drop_table('relationships')
    
    # Drop cardinality enum
    cardinality_enum = postgresql.ENUM('1:1', '1:N', 'N:M', name='cardinalitytype')
    cardinality_enum.drop(op.get_bind())
