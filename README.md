# Nigerian Property Valuation API

A small, explainable FastAPI portfolio project for recording property comparables and generating **indicative** estimates. It demonstrates how Estate Management domain knowledge can be translated into API design, data validation, persistence, tests, and transparent calculations.

> **Important:** this is an educational software demonstration, not a professional valuation, investment recommendation, or substitute for a qualified Nigerian Estate Surveyor and Valuer. Included sample records are synthetic and must never be represented as actual market transactions.

## Features

- CRUD endpoints for sale and rental comparables.
- Input validation for price, floor area, dates, property types, and descriptions.
- Filters for location, property type, transaction type, date window, and floor-area range.
- Pagination, 404 responses, and a clear `insufficient_data` valuation response.
- Explainable median unit-rate estimate, included comparable records, exclusions, and limitations.
- SQLite by default; PostgreSQL supported through `DATABASE_URL`.
- SQLAlchemy models, Alembic migration, pytest tests, and OpenAPI docs.

## Architecture

```text
app/
  main.py          FastAPI application and startup
  config.py        Environment configuration
  db.py            SQLAlchemy engine/session and local initialization
  models.py        Persistence model and DB constraints
  schemas.py       Pydantic request/response validation
  valuation.py     Baseline comparable selection and calculation
  api/routes.py    HTTP routes
migrations/         Alembic environment and initial migration
scripts/            Synthetic sample-data loader
tests/              API and calculation behavior tests
```

## Data schema

Each `comparables` record contains:
- `property_type`: flat, detached/semi-detached/terrace house, land, duplex, shop, or office.
- `transaction_type`: `sale` or `rent`. They are never mixed in one estimate.
- `location`, `floor_area_sqm`, `price` (NGN), `observed_date`, `source_description`.
- Optional `bedrooms`, `bathrooms`, `condition`, `title_status`, `notes`.
- `is_synthetic`: explicitly marks illustrative data.

For rental comparables, `price` is the rent amount for the period represented by the source record. **Only compare records that share the same rental period** (for example, annual rent with annual rent); this first version does not model the period as a separate field, so consistency must be enforced by the data collector.

## Valuation method and assumptions

The baseline is a simple comparable approach:
1. Match property type and transaction type.
2. Require exact location text match (case-insensitive); this is intentionally conservative and does not imply that a broad neighbourhood is homogeneous.
3. Exclude records with floor area outside 0.5x–2.0x the subject's area, records after the valuation date, and records older than three years. If both bedroom counts are present, exclude a difference greater than two.
4. When four or more candidates remain, flag rates below one-third or above three times the median unit rate as extreme outliers.
5. Calculate each eligible comparable's `price / floor_area_sqm` and take the median unit rate. Multiply it by the subject floor area to produce the indicative point estimate.
6. Show a descriptive range from the median rate to the highest eligible unit rate; it is **not** a confidence interval.

The `adjustment_factor` is reported as `1.0`: this version normalizes for area by using price per square metre, but does not apply separate condition, title, time, frontage, access, amenities, or negotiation adjustments. The range can be wide and estimates can be unstable when there are few records. At least three eligible comparables are required.

No claim is made that this method produces accurate valuations across Nigeria. Location and property characteristics, title, comparable quality, transaction terms, and market conditions require professional judgement. Synthetic examples are only for exercising the API.

## Setup (Windows Command Prompt)

Install Python 3.11 or newer. From a fresh clone, run:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python scripts\load_sample_data.py
uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

SQLite defaults to `valuation.db` in the project root. `DATABASE_URL` may be set in `.env` or the environment; the application currently reads environment variables directly, so if you want `.env` auto-loading, add `load_dotenv()` at startup or export variables in your shell. Windows CMD example for the current terminal:

```bat
set DATABASE_URL=sqlite:///./valuation.db
```

For PostgreSQL support, also install the optional driver with `pip install -r requirements-postgres.txt`. PostgreSQL URL example (use a provider-issued URL and protect credentials):

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/comparables` | Create comparable |
| `GET` | `/api/v1/comparables` | Filter and paginate |
| `GET` | `/api/v1/comparables/{id}` | Retrieve one |
| `PUT` | `/api/v1/comparables/{id}` | Replace/update all editable fields |
| `DELETE` | `/api/v1/comparables/{id}` | Delete |
| `POST` | `/api/v1/valuations/estimate` | Estimate subject property |

Filters include `location`, `property_type`, `transaction_type`, `observed_from`, `observed_to`, `min_area_sqm`, `max_area_sqm`, `limit` (1–100), and `offset`.

### Example: create a synthetic sale comparable

```json
{
  "property_type": "flat",
  "transaction_type": "sale",
  "location": "Calabar",
  "floor_area_sqm": 100,
  "price": 11000000,
  "observed_date": "2026-09-01",
  "source_description": "Synthetic example only",
  "bedrooms": 2,
  "bathrooms": 1,
  "condition": "not assessed",
  "title_status": "not verified",
  "is_synthetic": true
}
```

### Example: request an estimate

```json
{
  "property_type": "flat",
  "transaction_type": "sale",
  "location": "Calabar",
  "floor_area_sqm": 100,
  "valuation_date": "2026-10-01",
  "bedrooms": 2,
  "bathrooms": 1,
  "condition": "fair"
}
```

Response contains status, estimate in NGN, range, method, count, each comparable's price and unit rate, exclusions, assumptions, and limitations. If fewer than three eligible comparables exist, estimate fields are `null` and status is `insufficient_data`.

## Tests and checks

```bat
pytest -q
```

Tests cover CRUD, filters, invalid prices and future dates, insufficient data, sale/rent separation, median calculation, synthetic markers, and extreme outlier flagging.

## Migrations

Use Alembic for schema changes:

```bat
alembic upgrade head
alembic revision --autogenerate -m "describe schema change"
alembic downgrade -1
```

Review autogenerated migrations before applying them. The app also calls `create_all()` at startup to make a fresh local environment convenient; in deployed environments, run migrations as a release step and consider removing startup `create_all()` to keep schema changes explicit.

## GitHub publishing

1. Create a new empty repository on GitHub; do not commit `.env`, credentials, or a local database.
2. In the project folder:

```bat
git init
git add .
git commit -m "Build Nigerian Property Valuation API"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/nigerian-property-valuation-api.git
git push -u origin main
```

Replace the placeholder URL with your own repository URL; it is not a live link until you create the repository.

## Deployment guide

A straightforward path is a Python web service on Render, Railway, or another ASGI-compatible host, with a managed PostgreSQL database. Check each provider's current pricing, sleep behavior, free-tier availability, region support, and disk/database retention before deploying; these terms change frequently.

- Set `DATABASE_URL` as a secret environment variable. Use PostgreSQL, not a local SQLite file, for multi-instance/ephemeral container deployments.
- Build/install command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (adapt `$PORT` syntax to the host; Windows CMD is not the deployment shell).
- Run `alembic upgrade head` as a release/pre-deploy command if the host supports it.
- Confirm health at `/health`; review logs and test `/docs`.
- SQLite file persistence may be lost on hosts with ephemeral filesystems and is unsuitable for multiple concurrent app instances. Persistent disks may add cost and can restrict horizontal scaling. Managed PostgreSQL usually has separate pricing, backup, and connection limits.
- Do not publish real tenant data or sensitive title/owner information in a public demo.

No live deployment is included or claimed. Verify provider documentation and prices immediately before choosing a host.

## Security and future work

This starter has no authentication or role-based access control. Add authentication, rate limiting, audit logs, request-size limits, backups, observability, and a data-retention policy before production. Consider explicit rental-period fields, currency and price basis, geospatial neighbourhoods, evidence provenance, title/condition adjustment workflows, and professional review.

### Optional machine learning

Intentionally not included in this first version. No suitable verified, representative Nigerian property dataset was supplied, and synthesizing one would not support a credible model. Future ML work should use a licensed, documented dataset, reproducible train/test split, leakage-safe geographic/time validation, a simple baseline, and MAE/RMSE reporting. Geographic bias and small sample sizes must be disclosed.
