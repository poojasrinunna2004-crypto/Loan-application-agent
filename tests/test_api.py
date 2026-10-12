from fastapi.testclient import TestClient

from app import database
from app.api import app


def test_root_serves_browser_application():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Loan application" in response.text

    for asset_path in ("/static/styles.css", "/static/app.js"):
        asset = client.get(asset_path)
        assert asset.status_code == 200


def test_docs_serves_friendly_guide_and_swagger_remains_available():
    with TestClient(app) as client:
        guide = client.get("/docs")
        swagger = client.get("/swagger")

    assert guide.status_code == 200
    assert guide.headers["content-type"].startswith("text/html")
    assert "Quick start" in guide.text
    assert guide.text.count('class="response-summary"') == 3
    assert '"confirmation": true' in guide.text
    assert swagger.status_code == 200
    assert "Interactive API | Loan Studio" in swagger.text
    assert "/static/swagger.css" in swagger.text

    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/customers"]["get"]["tags"] == ["Getting started"]
    assert schema["paths"]["/applications"]["post"]["tags"] == ["Loan applications"]

    assert client.get("/static/swagger.css").status_code == 200


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
