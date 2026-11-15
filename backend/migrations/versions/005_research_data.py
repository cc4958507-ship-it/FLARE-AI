"""Native wide observations and a content-addressed research library."""
from alembic import op
import sqlalchemy as sa
revision = '005'
down_revision = '004'


def upgrade():
    op.create_table('source_observations',
        sa.Column('dataset_id',sa.String(64),sa.ForeignKey('datasets.id'),primary_key=True),
        sa.Column('seq',sa.Integer(),primary_key=True),
        sa.Column('t_rel_ms',sa.Integer(),nullable=False),
        sa.Column('source_time',sa.String(64),nullable=False),
        sa.Column('values_json',sa.JSON(),nullable=False),
        sa.Column('original_values',sa.JSON(),nullable=False),
        sa.Column('metadata_json',sa.JSON(),nullable=False))
    op.create_index('ix_source_observations_time','source_observations',['dataset_id','t_rel_ms','seq'])
    op.create_index('ix_measurements_channel_time','measurements',['dataset_id','channel','t_rel_ms','seq'])
    op.create_table('research_assets',sa.Column('id',sa.String(64),primary_key=True),sa.Column('payload',sa.JSON(),nullable=False))


def downgrade():
    op.drop_table('research_assets')
    op.drop_index('ix_measurements_channel_time',table_name='measurements')
    op.drop_table('source_observations')
