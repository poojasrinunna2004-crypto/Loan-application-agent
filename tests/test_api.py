from fastapi.testclient import TestClient

from app import database
from app.api import app


def test_root_redirects_to_api_docs():
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_submission_requires_explicit_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.initialize_database()

    with TestClient(app) as client:
        response = client.post(
            "/applications",
            json={
                "customer_id": 1,
                "loan_type": "personal",
                "amount": 12000,
                "term_months": 36,
                "purpose": "Home repairs",
            },
        )
        assert response.status_code == 201
        application_id = response.json()["id"]
        assert response.json()["status"] == "draft"

        denied = client.post(
            f"/applications/{application_id}/submit", json={"confirmation": False}
        )
        assert denied.status_code == 400
        coerced = client.post(
            f"/applications/{application_id}/submit", json={"confirmation": "true"}
        )
        assert coerced.status_code == 422
        assert client.get(f"/applications/{application_id}").json()["status"] == "draft"

        confirmed = client.post(
            f"/applications/{application_id}/submit", json={"confirmation": True}
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["status"] == "submitted"
        assert confirmed.json()["submitted_at"] is not None


def test_unknown_customer_cannot_create_application(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.initialize_database()

    with TestClient(app) as client:
        response = client.post(
            "/applications",
            json={
                "customer_id": 999,
                "loan_type": "auto",
                "amount": 15000,
                "term_months": 48,
                "purpose": "Used vehicle purchase",
            },
        )
    assert response.status_code == 404
