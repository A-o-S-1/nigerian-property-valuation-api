from datetime import date
from statistics import median
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Comparable
from app.schemas import SubjectProperty

MIN_COMPARABLES = 3

def estimate_property(db: Session, subject: SubjectProperty) -> dict:
    stmt = select(Comparable).where(
        Comparable.property_type == subject.property_type,
        Comparable.transaction_type == subject.transaction_type,
    )
    all_candidates = list(db.scalars(stmt).all())
    eligible, exclusions = [], []
    subject_location = subject.location.strip().casefold()
    for comp in all_candidates:
        reasons = []
        if comp.location.strip().casefold() != subject_location:
            reasons.append("location does not match exactly")
        size_ratio = comp.floor_area_sqm / subject.floor_area_sqm
        if not 0.5 <= size_ratio <= 2.0:
            reasons.append("floor area is outside 0.5x–2.0x subject size")
        age_days = (subject.valuation_date - comp.observed_date).days
        if age_days < 0:
            reasons.append("comparable date is after valuation date")
        elif age_days > 1095:
            reasons.append("comparable is older than 3 years")
        if subject.bedrooms is not None and comp.bedrooms is not None and abs(subject.bedrooms-comp.bedrooms) > 2:
            reasons.append("bedroom count differs by more than 2")
        if reasons:
            exclusions.append(f"Comparable {comp.id}: " + "; ".join(reasons))
        else:
            eligible.append(comp)

    # Robust median-rate filter: exclude extreme unit rates using a broad 3x median fence.
    rates = [c.price / c.floor_area_sqm for c in eligible]
    if len(rates) >= 4:
        med = median(rates)
        kept = []
        for c, rate in zip(eligible, rates):
            if rate < med / 3 or rate > med * 3:
                exclusions.append(f"Comparable {c.id}: unit rate flagged as an extreme outlier")
            else:
                kept.append(c)
        eligible = kept

    assumptions = [
        "Prices are interpreted in NGN; rental records must use a consistent stated rental period.",
        "Only exact location, property type, and transaction type matches are considered.",
        "A simple size adjustment is applied through price per square metre; no separate attribute premiums are estimated.",
        "The estimate uses the median adjusted unit rate, which is less sensitive to a single extreme observation.",
    ]
    limitations = [
        "Indicative educational estimate only; not a professional valuation or lending, tax, legal, or investment advice.",
        "Results depend on comparable quality, location granularity, title, condition, amenities, transaction terms, and market conditions.",
        "The sample may be small or synthetic and must not be treated as verified current Nigerian market evidence.",
        "No time, title, condition, floor, frontage, access, or negotiation adjustments are modelled.",
    ]
    if len(eligible) < MIN_COMPARABLES:
        return {
            "status": "insufficient_data", "estimate_ngn": None, "estimate_low_ngn": None,
            "estimate_high_ngn": None, "transaction_type": subject.transaction_type,
            "method": "Comparable approach: median price per square metre; size-adjusted to subject",
            "comparable_count": len(eligible), "comparables": [], "exclusions": exclusions,
            "assumptions": assumptions,
            "limitations": limitations + [f"At least {MIN_COMPARABLES} eligible comparables are required; add suitable records and retry."],
        }

    rates = [c.price / c.floor_area_sqm for c in eligible]
    median_rate = median(rates)
    used = []
    for c, rate in zip(eligible, rates):
        # Comparable unit rate already normalizes floor area. A small explicit size adjustment
        # is not applied; subject area multiplies the comparable's rate.
        used.append({
            "comparable_id": c.id, "location": c.location, "price_ngn": c.price,
            "floor_area_sqm": c.floor_area_sqm, "price_per_sqm_ngn": round(rate, 2),
            "observed_date": c.observed_date, "adjustment_factor": 1.0,
            "adjusted_rate_ngn_per_sqm": round(rate, 2),
            "source_description": c.source_description, "is_synthetic": c.is_synthetic,
        })
    point = median_rate * subject.floor_area_sqm
    # A descriptive dispersion band, not a statistical confidence interval.
    low = median([x["adjusted_rate_ngn_per_sqm"] for x in used]) * subject.floor_area_sqm
    high = max(x["adjusted_rate_ngn_per_sqm"] for x in used) * subject.floor_area_sqm
    return {
        "status": "estimate", "estimate_ngn": round(point, 2),
        "estimate_low_ngn": round(min(low, point), 2), "estimate_high_ngn": round(max(high, point), 2),
        "transaction_type": subject.transaction_type,
        "method": "Comparable approach: median comparable price per square metre × subject floor area",
        "comparable_count": len(used), "comparables": used, "exclusions": exclusions,
        "assumptions": assumptions,
        "limitations": limitations + ["The displayed range is the eligible comparable unit-rate range, not a confidence interval."],
    }
