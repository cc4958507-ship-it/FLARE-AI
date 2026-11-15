"""Preserve raw CSV and normalized experimental measurements separately."""
from alembic import op
import sqlalchemy as sa
revision = '002'
down_revision = '001'


def upgrade():
    op.create_table('datasets', sa.Column('id', sa.String(64), primary_key=True),
                    sa.Column('manifest', sa.JSON(), nullable=False),
                    sa.Column('raw_csv', sa.Text(), nullable=False),
                    sa.Column('report', sa.JSON(), nullable=False))
    op.create_table('measurements',
                    sa.Column('dataset_id', sa.String(64), sa.ForeignKey('datasets.id'), primary_key=True),
                    sa.Column('channel', sa.String(120), primary_key=True),
                    sa.Column('sensor_id', sa.String(120), primary_key=True),
                    sa.Column('seq', sa.Integer(), primary_key=True),
                    sa.Column('t_rel_ms', sa.Integer(), nullable=False),
                    sa.Column('value', sa.Float(), nullable=True),
                    sa.Column('metadata_json', sa.JSON(), nullable=False))
    op.create_index('ix_measurements_dataset_time', 'measurements', ['dataset_id', 't_rel_ms'])


def downgrade():
    op.drop_table('measurements')
    op.drop_table('datasets')
