"""Add two_factor_secret to User model

Revision ID: 31e8a2b21c04
Revises: 340aeb2d3c87
Create Date: 2024-08-22 22:47:46.604333

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31e8a2b21c04'
down_revision = '340aeb2d3c87'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('two_factor_secret', sa.String(length=16), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('two_factor_secret')

    # ### end Alembic commands ###
