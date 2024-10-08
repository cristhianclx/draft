"""empty message

Revision ID: d8062e0fe4d4
Revises: 893c0d02a0e7
Create Date: 2024-08-23 18:40:49.002818

"""

from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "d8062e0fe4d4"
down_revision = "893c0d02a0e7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("searches", schema=None) as batch_op:
        batch_op.alter_column("url", existing_type=mysql.VARCHAR(length=255), nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("searches", schema=None) as batch_op:
        batch_op.alter_column("url", existing_type=mysql.VARCHAR(length=255), nullable=False)

    # ### end Alembic commands ###
