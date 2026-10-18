import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client():
    # Import app after setting a temporary isolated SQLite DB for this test process.
    from app.db import Base, engine
    from app.main import app
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
