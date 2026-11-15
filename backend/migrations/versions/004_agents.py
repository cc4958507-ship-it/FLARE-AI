"""Durable agent jobs, step events and shared provider-call accounting."""
from alembic import op
import sqlalchemy as sa
revision = '004'
down_revision = '003'


def upgrade():
    op.create_table('agent_jobs',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('idempotency_key', sa.String(100), unique=True, nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('status', sa.String(24), nullable=False),
        sa.Column('input', sa.JSON(), nullable=False), sa.Column('checkpoint', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('max_calls', sa.Integer(), nullable=False), sa.Column('calls_used', sa.Integer(), nullable=False),
        sa.Column('retries', sa.Integer(), nullable=False),
        sa.Column('available_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lease_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lease_owner', sa.String(64), nullable=True), sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_agent_jobs_status', 'agent_jobs', ['status'])
    op.create_table('agent_events',
        sa.Column('job_id', sa.String(64), sa.ForeignKey('agent_jobs.id'), primary_key=True),
        sa.Column('seq', sa.Integer(), primary_key=True), sa.Column('payload', sa.JSON(), nullable=False))
    op.create_table('llm_calls',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('agent_jobs.id'), nullable=True),
        sa.Column('step', sa.Integer(), nullable=False), sa.Column('purpose', sa.String(64), nullable=False),
        sa.Column('state', sa.String(24), nullable=False), sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('response', sa.JSON(), nullable=True), sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('credits', sa.Numeric(12,6), nullable=True), sa.Column('reserved_credits', sa.Numeric(12,6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_llm_calls_job_id', 'llm_calls', ['job_id'])
    op.create_index('ix_llm_calls_created_at', 'llm_calls', ['created_at'])


def downgrade():
    for name in ('llm_calls', 'agent_events', 'agent_jobs'):
        op.drop_table(name)
