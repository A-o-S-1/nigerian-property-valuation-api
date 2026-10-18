from datetime import date
from sqlalchemy import String, Float, Date, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Comparable(Base):
    __tablename__ = "comparables"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_comparable_price_positive"),
        CheckConstraint("floor_area_sqm > 0", name="ck_comparable_area_positive"),
        CheckConstraint("bedrooms IS NULL OR bedrooms >= 0", name="ck_comparable_bedrooms_nonnegative"),
        Index("ix_comparable_location_type_date", "location", "property_type", "observed_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_type: Mapped[str] = mapped_column(String(40), index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), index=True)  # sale or rent
    location: Mapped[str] = mapped_column(String(160), index=True)
    floor_area_sqm: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    observed_date: Mapped[date] = mapped_column(Date, index=True)
    source_description: Mapped[str] = mapped_column(String(300))
    bedrooms: Mapped[int | None] = mapped_column(nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(nullable=True)
    condition: Mapped[str | None] = mapped_column(String(40), nullable=True)
    title_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(default=False, nullable=False)
