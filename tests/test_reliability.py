import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from rulereplay.lifecycle import RunTrace
from rulereplay.main import create_app
from rulereplay.operations import OperationError, Operations
from rulereplay.storage import Store


def test_illegal_and_terminal_transitions():
    trace = RunTrace()
    with pytest.raises(ValueError):
        trace.transition("COMPLETED")
    trace.transition("VALIDATING")
    trace.transition("EXECUTING")
    trace.transition("EVALUATING")
    trace.transition("NEEDS_REVIEW")
    with pytest.raises(ValueError):
        trace.transition("EXECUTING")


def test_durable_idempotency_reuses_evidence_and_rejects_conflict(settings):
    client = TestClient(create_app(settings))
    headers = {"Idempotency-Key": "same-request-123"}
    first = client.post("/api/verify", json={}, headers=headers)
    assert first.status_code == 201
    # New application simulates process restart; completed receipt survives.
    client = TestClient(create_app(settings))
    again = client.post("/api/verify", json={}, headers=headers)
    assert again.json() == first.json()
    assert len(list((settings.data_dir / "runs").glob("*.json"))) == 1
    assert (
        client.post("/api/verify", json={"scenario": "corrected"}, headers=headers).status_code
        == 409
    )


def test_inflight_capacity_never_starts_second_operation(settings):
    operations = Operations(settings)
    entered, release = Event(), Event()

    def slow(trace):
        entered.set()
        assert release.wait(3)
        return {"id": "unused"}

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(operations.run, "runs", {}, None, slow)
        assert entered.wait(3)
        try:
            with pytest.raises(OperationError) as error:
                operations.run("runs", {}, None, lambda _: pytest.fail("Must not execute"))
            assert error.value.status == 429
        finally:
            release.set()
        future.result()


def test_failed_claim_is_not_reexecuted(settings):
    operations = Operations(settings)

    def fail(_):
        raise RuntimeError("synthetic-sensitive-value")

    with pytest.raises(RuntimeError):
        operations.run("runs", {}, "interrupted-123", fail)
    with pytest.raises(OperationError, match="interrupted"):
        operations.run("runs", {}, "interrupted-123", lambda _: pytest.fail("No retry"))
    failures = list((settings.data_dir / "failures").glob("*.json"))
    assert failures and all("synthetic-sensitive-value" not in p.read_text() for p in failures)


def test_session_budget_and_live_key(settings):
    settings.max_model_calls_per_session = 1
    operations = Operations(settings)

    def result(_):
        return Store(settings.data_dir / "generations").save({"safe": True})

    with pytest.raises(OperationError, match="Idempotency"):
        operations.run("generations", {}, None, result, model_calls=1)
    operations.run("generations", {}, "first-call-123", result, model_calls=1)
    operations.run("generations", {}, "first-call-123", result, model_calls=1)
    assert operations.model_calls == 1
    with pytest.raises(OperationError, match="budget"):
        operations.run("generations", {}, "second-call-123", result, model_calls=1)


def test_storage_failure_is_sanitized_and_never_completed(settings, caplog):
    caplog.set_level("INFO", logger="rulereplay.events")
    client = TestClient(create_app(settings))
    with patch.object(Store, "save", side_effect=OSError("synthetic-sensitive-path")):
        response = client.post("/api/verify", json={})
    assert response.status_code == 503
    assert response.json()["code"] == "storage_unavailable"
    assert "synthetic-sensitive" not in response.text + caplog.text
    transitions = [json.loads(r.message) for r in caplog.records]
    assert any(t.get("state") == "FAILED" for t in transitions)
    assert not any(t.get("state") == "COMPLETED" for t in transitions)


@pytest.mark.parametrize("key", ["../.env", "x" * 129, "a"])
def test_invalid_idempotency_header(settings, key):
    response = TestClient(create_app(settings)).post(
        "/api/verify", json={}, headers={"Idempotency-Key": key}
    )
    assert response.status_code == 422


def test_unknown_record_and_unexpected_error_are_safe(settings):
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    assert client.get("/api/runs/" + "f" * 32).status_code == 409
    with patch("rulereplay.api.verify", side_effect=RuntimeError("synthetic-sensitive-detail")):
        response = client.post("/api/verify", json={})
    assert response.status_code == 500
    assert "synthetic-sensitive" not in response.text


def test_unexpected_exception_does_not_escape_to_server_logger(settings, caplog):
    caplog.set_level("INFO", logger="rulereplay.events")
    client = TestClient(create_app(settings))  # Would raise if error escaped middleware.
    with patch("rulereplay.api.verify", side_effect=RuntimeError("private-unexpected-value")):
        response = client.post("/api/verify", json={})
    assert response.status_code == 500
    assert response.json()["correlation_id"] == response.headers["x-correlation-id"]
    assert "private-unexpected-value" not in caplog.text + response.text


def test_configurable_request_limit(settings):
    settings.max_request_bytes = 1024
    client = TestClient(create_app(settings))
    assert client.post("/api/verify", content=b"x" * 1025).status_code == 413
