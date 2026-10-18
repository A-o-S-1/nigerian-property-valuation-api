from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

PropertyType = Literal["flat", "detached_house", "semi_detached_house", "terrace_house", "land", "duplex", "shop", "office"]
TransactionType = Literal["sale", "rent"]

class ComparableBase(BaseModel):
    property_type: PropertyType
    transaction_type: TransactionType
    location: str = Field(min_length=2, max_length=160)
    floor_area_sqm: float = Field(gt=0, le=100000)
    price: float = Field(gt=0, le=1e15, description="NGN; rent is the stated rental period's total")
    observed_date: date
    source_description: str = Field(min_length=3, max_length=300)
    bedrooms: int | None = Field(default=None, ge=0, le=100)
    bathrooms: int | None = Field(default=None, ge=0, le=100)
    condition: str | None = Field(default=None, max_length=40)
    title_status: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)
    is_synthetic: bool = False

    @field_validator("location", "source_description")
    @classmethod
    def strip_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("observed_date")
    @classmethod
    def date_not_future(cls, value):
        if value > date.today():
            raise ValueError("observed_date cannot be in the future")
        return value

class ComparableCreate(ComparableBase):
    pass

class ComparableUpdate(ComparableBase):
    pass

class ComparableRead(ComparableBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ComparablePage(BaseModel):
    items: list[ComparableRead]
    total: int
    limit: int
    offset: int

class SubjectProperty(BaseModel):
    property_type: PropertyType
    transaction_type: TransactionType
    location: str = Field(min_length=2, max_length=160)
    floor_area_sqm: float = Field(gt=0, le=100000)
    valuation_date: date = Field(default_factory=date.today)
    bedrooms: int | None = Field(default=None, ge=0, le=100)
    bathrooms: int | None = Field(default=None, ge=0, le=100)
    condition: str | None = Field(default=None, max_length=40)

    @field_validator("valuation_date")
    @classmethod
    def valuation_date_not_future(cls, value):
        if value > date.today():
            raise ValueError("valuation_date cannot be in the future")
        return value

class UsedComparable(BaseModel):
    comparable_id: int
    location: str
    price_ngn: float
    floor_area_sqm: float
    price_per_sqm_ngn: float
    observed_date: date
    adjustment_factor: float
    adjusted_rate_ngn_per_sqm: float
    source_description: str
    is_synthetic: bool

class ValuationResponse(BaseModel):
    status: Literal["estimate", "insufficient_data"]
    estimate_ngn: float | None
    estimate_low_ngn: float | None
    estimate_high_ngn: float | None
    currency: str = "NGN"
    transaction_type: TransactionType
    method: str
    comparable_count: int
    comparables: list[UsedComparable]
    exclusions: list[str]
    assumptions: list[str]
    limitations: list[str]
