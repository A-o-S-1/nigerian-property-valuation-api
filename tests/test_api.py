from datetime import date, timedelta

def payload(**kwargs):
    base = {
        "property_type": "flat", "transaction_type": "sale", "location": "Calabar",
        "floor_area_sqm": 100, "price": 10000000,
        "observed_date": (date.today()-timedelta(days=30)).isoformat(),
        "source_description": "Illustrative synthetic comparable", "bedrooms": 2,
        "bathrooms": 2, "condition": "fair", "title_status": "not verified",
        "is_synthetic": True,
    }
    base.update(kwargs)
    return base

def test_crud_and_filter(client):
    r = client.post("/api/v1/comparables", json=payload())
    assert r.status_code == 201, r.text
    item_id = r.json()["id"]
    assert client.get(f"/api/v1/comparables/{item_id}").status_code == 200
    assert client.get("/api/v1/comparables?location=Calabar&transaction_type=sale").json()["total"] == 1
    updated = payload(price=12000000)
    assert client.put(f"/api/v1/comparables/{item_id}", json=updated).json()["price"] == 12000000
    assert client.delete(f"/api/v1/comparables/{item_id}").status_code == 204
    assert client.get(f"/api/v1/comparables/{item_id}").status_code == 404

def test_invalid_price_and_future_date(client):
    assert client.post("/api/v1/comparables", json=payload(price=-1)).status_code == 422
    future = (date.today()+timedelta(days=1)).isoformat()
    assert client.post("/api/v1/comparables", json=payload(observed_date=future)).status_code == 422

def test_insufficient_comparables(client):
    response = client.post("/api/v1/valuations/estimate", json={
        "property_type": "flat", "transaction_type": "sale", "location": "Calabar",
        "floor_area_sqm": 100, "valuation_date": date.today().isoformat(), "bedrooms": 2
    })
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert response.json()["estimate_ngn"] is None

def test_estimate_median_and_transaction_separation(client):
    for price, area in [(10000000,100),(12000000,100),(11000000,100)]:
        assert client.post("/api/v1/comparables", json=payload(price=price, floor_area_sqm=area)).status_code == 201
    # A rent record must not contaminate a sale estimate.
    client.post("/api/v1/comparables", json=payload(transaction_type="rent", price=300000))
    response = client.post("/api/v1/valuations/estimate", json={
        "property_type":"flat","transaction_type":"sale","location":"Calabar",
        "floor_area_sqm":100,"valuation_date":date.today().isoformat(),"bedrooms":2
    })
    data = response.json()
    assert data["status"] == "estimate"
    assert data["estimate_ngn"] == 11000000
    assert data["comparable_count"] == 3
    assert all(c["is_synthetic"] for c in data["comparables"])

def test_outlier_flagged_when_four_or_more(client):
    for price in [10000000, 11000000, 12000000, 1000000000]:
        client.post("/api/v1/comparables", json=payload(price=price))
    response = client.post("/api/v1/valuations/estimate", json={
        "property_type":"flat","transaction_type":"sale","location":"Calabar",
        "floor_area_sqm":100,"valuation_date":date.today().isoformat()
    })
    data = response.json()
    assert any("outlier" in item for item in data["exclusions"])
