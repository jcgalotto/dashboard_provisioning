from fastapi.testclient import TestClient

from app.main import app


class DummyUser:
    token = "token"


def auth_header():
    return {"Authorization": "Bearer dummy"}


def test_list_interfaces(monkeypatch):
    def fake_fetch_page(query, params, limit, offset):
        return [{"pri_id": 1, "pri_cellular_number": "123", "pri_status": "OK"}]

    monkeypatch.setattr("app.db.oracle.fetch_page", fake_fetch_page)
    monkeypatch.setattr("app.core.deps.decode_token", lambda token: "user")

    client = TestClient(app)
    resp = client.get("/provisioning/interfaces", headers=auth_header())
    assert resp.status_code == 200
    assert resp.json()["data"][0]["pri_id"] == 1
