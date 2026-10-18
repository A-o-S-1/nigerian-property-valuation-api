"""create comparables table"""
from alembic import op
import sqlalchemy as sa
revision = "0001_comparables"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "comparables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_type", sa.String(length=40), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("floor_area_sqm", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("observed_date", sa.Date(), nullable=False),
        sa.Column("source_description", sa.String(length=300), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Integer(), nullable=True),
        sa.Column("condition", sa.String(length=40), nullable=True),
        sa.Column("title_status", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("price > 0", name="ck_comparable_price_positive"),
        sa.CheckConstraint("floor_area_sqm > 0", name="ck_comparable_area_positive"),
        sa.CheckConstraint("bedrooms IS NULL OR bedrooms >= 0", name="ck_comparable_bedrooms_nonnegative"),
    )
    op.create_index("ix_comparables_id", "comparables", ["id"])
    op.create_index("ix_comparables_property_type", "comparables", ["property_type"])
    op.create_index("ix_comparables_transaction_type", "comparables", ["transaction_type"])
    op.create_index("ix_comparables_location", "comparables", ["location"])
    op.create_index("ix_comparables_observed_date", "comparables", ["observed_date"])
    op.create_index("ix_comparable_location_type_date", "comparables", ["location","property_type","observed_date"])

def downgrade():
    op.drop_table("comparables")
