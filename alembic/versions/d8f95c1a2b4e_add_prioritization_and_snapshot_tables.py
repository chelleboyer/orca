from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'd8f95c1a2b4e'
down_revision = 'a8f75715ae5b'
branch_labels = None
depends_on = None


def upgrade():
    # Create prioritizations table using existing enum types
    op.create_table('prioritizations',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('item_type', sa.Enum('object', 'cta', 'attribute', 'relationship', name='itemtype', create_type=False), nullable=False),
        sa.Column('item_id', UUID(as_uuid=True), nullable=False),
        sa.Column('priority_phase', sa.Enum('now', 'next', 'later', 'unassigned', name='priorityphase', create_type=False), nullable=True, default='unassigned'),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True, default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('assigned_by', UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create prioritization_snapshots table
    op.create_table('prioritization_snapshots',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('snapshot_data', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_prioritizations_project_item', 'prioritizations', ['project_id', 'item_type', 'item_id'])
    op.create_index('idx_prioritizations_phase_position', 'prioritizations', ['project_id', 'priority_phase', 'position'])
    op.create_index('idx_prioritization_snapshots_project', 'prioritization_snapshots', ['project_id', 'created_at'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_prioritization_snapshots_project')
    op.drop_index('idx_prioritizations_phase_position')
    op.drop_index('idx_prioritizations_project_item')
    
    # Drop tables
    op.drop_table('prioritization_snapshots')
    op.drop_table('prioritizations')
    
    # Drop the enums
    op.execute("DROP TYPE IF EXISTS priorityphase")
    op.execute("DROP TYPE IF EXISTS itemtype")
