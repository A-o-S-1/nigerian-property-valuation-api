from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Comparable
from app.schemas import ComparableCreate, ComparableUpdate, ComparableRead, ComparablePage, SubjectProperty, ValuationResponse
from app.valuation import estimate_property

router = APIRouter()

@router.post("/comparables", response_model=ComparableRead, status_code=201, tags=["comparables"])
def create_comparable(payload: ComparableCreate, db: Session = Depends(get_db)):
    record = Comparable(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/comparables", response_model=ComparablePage, tags=["comparables"])
def list_comparables(
    location: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = Query(default=None, pattern="^(sale|rent)$"),
    observed_from: date | None = None,
    observed_to: date | None = None,
    min_area_sqm: float | None = Query(default=None, gt=0),
    max_area_sqm: float | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if observed_from and observed_to and observed_from > observed_to:
        raise HTTPException(422, "observed_from must be on or before observed_to")
    if min_area_sqm and max_area_sqm and min_area_sqm > max_area_sqm:
        raise HTTPException(422, "min_area_sqm must be <= max_area_sqm")
    stmt = select(Comparable)
    if location: stmt = stmt.where(func.lower(Comparable.location) == location.strip().lower())
    if property_type: stmt = stmt.where(Comparable.property_type == property_type)
    if transaction_type: stmt = stmt.where(Comparable.transaction_type == transaction_type)
    if observed_from: stmt = stmt.where(Comparable.observed_date >= observed_from)
    if observed_to: stmt = stmt.where(Comparable.observed_date <= observed_to)
    if min_area_sqm is not None: stmt = stmt.where(Comparable.floor_area_sqm >= min_area_sqm)
    if max_area_sqm is not None: stmt = stmt.where(Comparable.floor_area_sqm <= max_area_sqm)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Comparable.observed_date.desc(), Comparable.id.desc()).offset(offset).limit(limit)).all()
    return {"items": rows, "total": total or 0, "limit": limit, "offset": offset}

@router.get("/comparables/{comparable_id}", response_model=ComparableRead, tags=["comparables"])
def get_comparable(comparable_id: int, db: Session = Depends(get_db)):
    record = db.get(Comparable, comparable_id)
    if not record: raise HTTPException(404, "Comparable not found")
    return record

@router.put("/comparables/{comparable_id}", response_model=ComparableRead, tags=["comparables"])
def update_comparable(comparable_id: int, payload: ComparableUpdate, db: Session = Depends(get_db)):
    record = db.get(Comparable, comparable_id)
    if not record: raise HTTPException(404, "Comparable not found")
    for key, value in payload.model_dump().items(): setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

@router.delete("/comparables/{comparable_id}", status_code=204, tags=["comparables"])
def delete_comparable(comparable_id: int, db: Session = Depends(get_db)):
    record = db.get(Comparable, comparable_id)
    if not record: raise HTTPException(404, "Comparable not found")
    db.delete(record)
    db.commit()
    return Response(status_code=204)

@router.post("/valuations/estimate", response_model=ValuationResponse, tags=["valuation"])
def valuation(payload: SubjectProperty, db: Session = Depends(get_db)):
    return estimate_property(db, payload)
