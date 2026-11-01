import pytest
from fastapi.testclient import TestClient
from rulereplay import api
from rulereplay.main import create_app


def test_full_offline_workflow(settings):
    client = TestClient(create_app(settings))
    assert client.get("/api/policies").status_code == 200
    assert len(client.get("/api/fixtures").json()) == 5
    generated = client.post("/api/generate", json={"mode": "offline"})
    assert generated.status_code == 201
    record = client.post("/api/verify", json={"generation_id": generated.json()["id"]})
    assert record.status_code == 201
    data = record.json()
    assert data["summary"]["counts"]["unauthorized_regression"] > 0
    assert client.get("/api/runs").json()[0]["id"] == data["id"]
    assert client.get(f"/api/runs/{data['id']}").json() == data
    assert client.post(f"/api/runs/{data['id']}/replay").json()["consistent"]


@pytest.mark.parametrize("outcome", ["PASS", "FAIL", "REVIEW", "UNVERIFIED", None])
def test_history_preserves_authoritative_release_verdict(settings, monkeypatch, outcome):
    # Projection contract only, not evidence of a live PASS or a provider execution.
    record = {
        "id": "synthetic-history",
        "created_at": "2026-10-29T12:00:00Z",
        "scenario": "corrected",
        "summary": {"decision": "pass"},
        "execution_mode": "modal" if outcome == "PASS" else "simulator",
        "sources": {"python": "not part of the history projection"},
    }
    if outcome is not None:
        record["release"] = {"outcome": outcome, "reason": "Synthetic contract test"}

    class HistoryStore:
        def recent(self):
            return [record]

    monkeypatch.setattr(api, "stores", lambda request: {"runs": HistoryStore()})
    item = TestClient(create_app(settings)).get("/api/runs").json()[0]
    assert item["release"] == record.get("release")
    assert item["summary"]["decision"] == "pass"  # Compatibility is unchanged.
    assert "sources" not in item


def test_successful_offline_run_stays_unverified_in_history_details_and_replay(settings):
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/verify",
        json={
            "scenario": "corrected",
            "cases": [{"id": "green", "due_date": "2026-11-01", "payment_date": "2026-11-01"}],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["summary"]["decision"] == "pass"
    assert data["release"]["outcome"] == "UNVERIFIED"
    assert client.get("/api/runs").json()[0]["release"] == data["release"]
    assert client.get(f"/api/runs/{data['id']}").json()["release"] == data["release"]
    assert client.post(f"/api/runs/{data['id']}/replay").json()["consistent"]
    assert client.get(f"/api/runs/{data['id']}").json()["release"] == data["release"]


def test_paid_routes_blocked(settings):
    client = TestClient(create_app(settings))
    assert client.post("/api/generate", json={"mode": "meta"}).status_code == 409
    assert client.post("/api/verify", json={"mode": "modal"}).status_code == 409


def test_browser_boundary_and_sanitized_validation(settings):
    client = TestClient(create_app(settings))
    response = client.post("/api/verify", json={}, headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403
    assert client.get("/api/health", headers={"Host": "untrusted.example"}).status_code == 400
    response = client.post("/api/verify", json={"mode": "synthetic-sensitive-string"})
    assert response.status_code == 422
    assert "synthetic-sensitive-string" not in response.text
    assert client.post("/api/verify", content=b"x" * 256001).status_code == 413


def test_changed_source_requires_regeneration(settings):
    client = TestClient(create_app(settings))
    suite = client.post("/api/generate", json={}).json()
    response = client.post(
        "/api/verify", json={"generation_id": suite["id"], "scenario": "corrected"}
    )
    assert response.status_code == 409


def test_policy_snapshots_are_immutable(settings):
    client = TestClient(create_app(settings))
    original = client.get("/api/policies").json()
    result = client.post("/api/policy-sets", json=original)
    assert result.status_code == 201
    assert client.get("/api/policies").json() == original
    assert client.get("/api/policy-sets").json()[0]["id"] == result.json()["id"]
