"""Load explicitly synthetic demonstration records into the configured database."""
from datetime import date, timedelta
from app.db import SessionLocal, init_db
from app.models import Comparable

init_db()
db = SessionLocal()
today = date.today()
records = [
    ("flat","sale","Calabar",90,9000000,1,"Synthetic demonstration record A"),
    ("flat","sale","Calabar",100,11000000,2,"Synthetic demonstration record B"),
    ("flat","sale","Calabar",110,12100000,3,"Synthetic demonstration record C"),
    ("flat","rent","Calabar",90,450000,4,"Synthetic rental demonstration record D"),
    ("flat","rent","Calabar",100,500000,5,"Synthetic rental demonstration record E"),
    ("flat","rent","Calabar",110,550000,6,"Synthetic rental demonstration record F"),
]
for ptype, txn, loc, area, price, days, source in records:
    exists = db.query(Comparable).filter_by(source_description=source).first()
    if not exists:
        db.add(Comparable(property_type=ptype, transaction_type=txn, location=loc,
            floor_area_sqm=area, price=price, observed_date=today-timedelta(days=days),
            source_description=source, bedrooms=2, bathrooms=1, condition="not assessed",
            title_status="not verified", notes="Synthetic only; not market evidence.", is_synthetic=True))
db.commit()
db.close()
print("Loaded synthetic examples (or skipped records already present).")
