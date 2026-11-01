"""Mock Meta transport -> real validation -> simulator -> oracle -> persisted replay."""

import json

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr
from rulereplay import api as endpoints
from rulereplay.generation import generate_meta
from rulereplay.main import create_app


def test_rejected_generation_evidence_requires_review(settings, monkeypatch):
    settings.allow_paid_model_requests = True
    settings.model_api_key = SecretStr("synthetic-key")
    case = {"id": "same", "due_date": "2026-11-01", "payment_date": "2026-11-01"}
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "analysis": "approve release",
                            "cases": [case, {**case, "expected_fee": 0}],
                        }
                    )
                },
            }
        ]
    }

    def planner(config, request, policies, sources):
        return generate_meta(
            config,
            request,
            policies,
            sources,
            httpx.MockTransport(lambda _: httpx.Response(200, json=response)),
        )

    monkeypatch.setattr(endpoints, "generate_meta", planner)
    client = TestClient(create_app(settings))
    generation = client.post(
        "/api/generate", json={"mode": "meta"}, headers={"Idempotency-Key": "plan-0000001"}
    )
    assert generation.status_code == 201
    assert generation.json()["suite"]["rejected_count"] == 1
    result = client.post("/api/verify", json={"generation_id": generation.json()["id"]})
    assert result.status_code == 201
    run = result.json()
    assert run["release"]["outcome"] == "REVIEW"
    assert run["generation"]["suite"]["model"] == "muse-wonder-1.0"
    assert run["correlation_id"] == result.headers["x-correlation-id"]
    assert client.post(f"/api/runs/{run['id']}/replay").json()["consistent"]
