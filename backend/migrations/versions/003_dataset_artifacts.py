"""Preserve original NASA file bytes alongside normalized measurements."""
from alembic import op
import sqlalchemy as sa
revision = '003'
down_revision = '002'


def upgrade():
    op.create_table('dataset_artifacts',
        sa.Column('dataset_id', sa.String(64), sa.ForeignKey('datasets.id'), primary_key=True),
        sa.Column('name', sa.String(120), primary_key=True),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False))


def downgrade():
    op.drop_table('dataset_artifacts')
