import json
from copy import deepcopy

import pytest
from rulereplay.domain import ExecutionResult
from rulereplay.integrity import digest
from rulereplay.policies import load_policies
from rulereplay.storage import RecordError, Store
from rulereplay.verification import VerifyRequest, replay, verify


def record(settings, tmp_path, **kwargs):
    return verify(
        VerifyRequest(**kwargs),
        settings,
        load_policies(),
        Store(tmp_path / "runs"),
        Store(tmp_path / "generations"),
    )


@pytest.mark.parametrize(
    "mutation",
    ["policy_hash", "source_hash", "missing_case", "missing_output", "duplicate", "generation"],
)
def test_rehashed_outer_record_cannot_hide_inconsistent_context(settings, tmp_path, mutation):
    saved = record(settings, tmp_path)
    if mutation == "policy_hash":
        saved["policies"]["policies"][0]["fee_cents"] = 100
    elif mutation == "source_hash":
        saved["sources"]["python"] += "\n# changed"
    elif mutation == "missing_case":
        saved["findings"][0]["case"] = None
    elif mutation == "missing_output":
        saved["findings"][0]["legacy"] = None
    elif mutation == "duplicate":
        saved["findings"].append(saved["findings"][0])
    else:
        saved["generation"] = {"source_sha256": {}, "suite": {"policy_sha256": "bad"}}
    with pytest.raises(RecordError):
        replay(saved)
    saved.pop("integrity_sha256")
    saved["integrity_sha256"] = digest(saved)
    (tmp_path / "runs" / (saved["id"] + ".json")).write_text(json.dumps(saved))
    with pytest.raises(RecordError):
        Store(tmp_path / "runs").get(saved["id"])


@pytest.mark.parametrize("field", ["reason", "verdict", "oracle", "summary", "release"])
def test_replay_detects_semantic_mismatch(settings, tmp_path, field):
    saved = record(settings, tmp_path)
    if field == "reason":
        saved["findings"][0]["reason"] = "Invented explanation"
    elif field == "verdict":
        saved["findings"][0]["verdict"] = "compliant"
    elif field == "oracle":
        saved["findings"][0]["oracle"]["fee_cents"] = 0
    elif field == "summary":
        saved["summary"]["decision"] = "pass"
    else:
        saved["release"]["outcome"] = "PASS"
    result = replay(saved)
    assert not result["consistent"] and result["outcome"] == "REPLAY_MISMATCH"


def test_offline_green_is_unverified_and_replay_is_deterministic(settings, tmp_path):
    saved = record(
        settings,
        tmp_path,
        cases=[
            {"id": "same", "due_date": "2026-11-01", "payment_date": "2026-11-01"},
        ],
    )
    assert saved["release"]["outcome"] == "UNVERIFIED"
    assert saved["lifecycle"]["state"] == "NEEDS_REVIEW"
    assert replay(saved) == replay(deepcopy(saved))


def test_execution_failure_requires_review(settings, tmp_path):
    saved = record(settings, tmp_path, scenario="execution_error")
    assert saved["release"]["outcome"] == "REVIEW"
    assert saved["summary"]["counts"]["unauthorized_regression"] == 0


def test_mocked_live_gateway_all_green(settings, tmp_path):
    # Labels describe the requested adapter mode; this is a mock integration test only.
    settings.allow_billable_modal = True
    settings.modal_token_id = "synthetic-id"
    settings.modal_token_secret = "synthetic-secret"
    from pydantic import SecretStr

    settings.modal_token_id = SecretStr("synthetic-id")
    settings.modal_token_secret = SecretStr("synthetic-secret")

    class Gateway:
        def run(self, language, source, case):
            return ExecutionResult(status="ok", fee_cents=0)

    saved = verify(
        VerifyRequest(
            mode="modal",
            cases=[
                {"id": "one", "due_date": "2026-11-01", "payment_date": "2026-11-01"},
            ],
        ),
        settings,
        load_policies(),
        Store(tmp_path),
        Store(tmp_path / "g"),
        executor=Gateway(),
    )
    assert saved["release"]["outcome"] == "PASS"
    assert saved["metrics"]["sandbox_executions"] == 2
    assert saved["lifecycle"]["state"] == "COMPLETED"
    assert replay(saved)["consistent"]


def test_replay_reports_runtime_context_changes(settings, tmp_path):
    saved = record(settings, tmp_path)
    saved["runtime"]["harness_sha256"] = "historical-harness"
    result = replay(saved)
    assert result["consistent"]  # Existing observations, not a new execution claim.
    assert result["context_differences"] == ["harness_sha256"]


def test_conclusive_failure_with_policy_gaps_is_not_marked_completed(settings, tmp_path):
    saved = record(settings, tmp_path)
    assert saved["release"]["outcome"] == "FAIL"
    assert saved["summary"]["unresolved"] > 0
    assert saved["lifecycle"]["state"] == "NEEDS_REVIEW"
