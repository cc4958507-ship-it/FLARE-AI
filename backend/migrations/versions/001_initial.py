"""Initial persisted entities, runs, immutable frames and ordered audit events."""
from alembic import op
import sqlalchemy as sa
revision = '001'
down_revision = None

def upgrade():
    op.create_table('records', sa.Column('id', sa.String(64), primary_key=True), sa.Column('kind', sa.String(32), nullable=False), sa.Column('payload', sa.JSON(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_records_kind', 'records', ['kind'])
    op.create_table('runs', sa.Column('id', sa.String(64), primary_key=True), sa.Column('payload', sa.JSON(), nullable=False), sa.Column('revision', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('frames', sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id'), primary_key=True), sa.Column('t', sa.Integer(), primary_key=True), sa.Column('sample', sa.JSON(), nullable=False), sa.Column('decision', sa.JSON(), nullable=False))
    op.create_table('audit_events', sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id'), primary_key=True), sa.Column('seq', sa.Integer(), primary_key=True), sa.Column('payload', sa.JSON(), nullable=False))

def downgrade():
    for name in ['audit_events', 'frames', 'runs', 'records']:
        op.drop_table(name)
