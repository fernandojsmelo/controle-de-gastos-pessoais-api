import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app as fastapi_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "teste.db")
    with TestClient(fastapi_app) as test_client:
        yield test_client
