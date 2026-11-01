import json

import pytest
from pydantic import ValidationError
from rulereplay.policies import load_policies
from rulereplay.storage import RecordError, Store
from rulereplay.verification import VerifyRequest, replay, verify


def test_run_and_replay(settings, tmp_path):
    store = Store(tmp_path / "runs")
    record = verify(VerifyRequest(), settings, load_policies(), store, Store(tmp_path / "suites"))
    assert record["summary"]["decision"] == "hold"
    assert record["summary"]["counts"]["unauthorized_regression"] >= 1
    assert record["summary"]["counts"]["authorized_policy_change"] >= 1
    assert replay(store.get(record["id"]))["consistent"] is True
    assert record["execution_mode"] == "simulator"


def test_invalid_input_and_duplicate_cases(settings, tmp_path):
    raw = {"id": "a", "due_date": "2026-11-01", "payment_date": "2026-11-07"}
    result = verify(
        VerifyRequest(cases=[raw, {**raw, "id": "b"}, {"id": "bad"}]),
        settings,
        load_policies(),
        Store(tmp_path),
        Store(tmp_path / "suites"),
    )
    assert result["duplicates_removed"] == 1
    assert result["summary"]["counts"]["invalid_input"] == 1
    assert result["summary"]["decision"] == "review"


def test_tampering_detected(tmp_path):
    store = Store(tmp_path)
    record = store.save({"test": "original"})
    file = tmp_path / (record["id"] + ".json")
    changed = json.loads(file.read_text())
    changed["test"] = "changed"
    file.write_text(json.dumps(changed))
    with pytest.raises(RecordError, match="integrity"):
        store.get(record["id"])


def test_path_traversal_rejected(tmp_path):
    with pytest.raises(RecordError):
        Store(tmp_path).get("../.env")


def test_submitted_code_cannot_use_local_simulator():
    with pytest.raises(ValidationError, match="only in Modal"):
        VerifyRequest(java_source="public class LegacyLoan {}", python_source="print(0)")


@pytest.mark.parametrize("invalid_first", [False, True])
def test_invalid_finding_ids_never_collide_with_user_cases(settings, tmp_path, invalid_first):
    valid = {"id": "invalid-2", "due_date": "2026-10-30", "payment_date": "2026-11-05"}
    invalid = {"id": "bad"}
    cases = [invalid, valid] if invalid_first else [valid, invalid]
    result = verify(
        VerifyRequest(cases=cases),
        settings,
        load_policies(),
        Store(tmp_path),
        Store(tmp_path / "suites"),
    )
    findings = result["findings"]
    assert len({finding["case_id"] for finding in findings}) == 2
    assert next(f for f in findings if f["case"] is not None)["case_id"] == "invalid-2"
    assert next(f for f in findings if f["case"] is None)["case_id"].startswith("invalid:")
    assert replay(result)["consistent"] is True


@pytest.mark.parametrize(
    "payload",
    [
        [],
        None,
        42,
        "string",
        {},
        {
            "id": "a" * 32,
            "integrity_sha256": [],
        },
        {"id": "a" * 32, "integrity_sha256": "not-a-digest"},
    ],
)
def test_malformed_evidence_shapes_raise_safe_record_error(tmp_path, payload):
    record_id = "a" * 32
    (tmp_path / (record_id + ".json")).write_text(json.dumps(payload))
    with pytest.raises(RecordError, match="missing or invalid"):
        Store(tmp_path).get(record_id)
