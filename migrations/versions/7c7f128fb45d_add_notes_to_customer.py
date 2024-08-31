"""Add notes to Customer

Revision ID: 7c7f128fb45d
Revises: 24a25eb40a09
Create Date: 2024-08-12 21:28:13.836306

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c7f128fb45d'
down_revision = '24a25eb40a09'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.drop_column('notes')

    # ### end Alembic commands ###
