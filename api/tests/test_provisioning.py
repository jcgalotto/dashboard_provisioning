from fastapi.testclient import TestClient

from app.main import app


def auth_header():
    return {"Authorization": "Bearer dummy"}


def test_list_interfaces(monkeypatch):
    captured = {}

    def fake_fetch_all(query, params, limit=None, offset=None):
        captured.update({"params": params, "limit": limit, "offset": offset})
        return [
            {
                "pri_id": 1,
                "pri_cellular_number": "123",
                "pri_status": "OK",
                "pri_action_date": "2020-01-01T00:00:00",
            }
        ]

    def fake_fetch_one(query, params=None):
        return {"cnt": 1}

    monkeypatch.setattr("app.db.queries.fetch_all", fake_fetch_all)
    monkeypatch.setattr("app.db.queries.fetch_one", fake_fetch_one)
    monkeypatch.setattr("app.core.deps.decode_token", lambda token: "user")

    client = TestClient(app)
    resp = client.get(
        "/provisioning/interfaces?page=2&page_size=10&status=OK",
        headers=auth_header(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert captured["limit"] == 10
    assert captured["offset"] == 10
    assert captured["params"]["status"] == "OK"
