"""Added profile_picture to Customer

Revision ID: 342be86510ea
Revises: e901e97bb836
Create Date: 2024-08-24 23:51:21.357353

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '342be86510ea'
down_revision = 'e901e97bb836'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')

    # ### end Alembic commands ###
