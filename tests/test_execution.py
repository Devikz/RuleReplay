import json
from unittest.mock import MagicMock

import pytest
from modal.exception import ExecTimeoutError, SandboxTimeoutError
from rulereplay.config import ConfigurationError, Settings
from rulereplay.domain import TestCase
from rulereplay.execution import ModalExecutor


def test_modal_disabled_never_touches_sdk(settings):
    sdk = MagicMock()
    with pytest.raises(ConfigurationError):
        ModalExecutor(settings, sdk).run(
            "python",
            "print(0)",
            TestCase(id="one", due_date="2026-11-01", payment_date="2026-11-01"),
        )
    assert not sdk.mock_calls


@pytest.mark.parametrize("failure", [False, True])
def test_modal_limits_and_cleanup(failure):
    sdk = MagicMock()
    sandbox = sdk.Sandbox.create.return_value
    process = MagicMock()
    process.stdout.__iter__.return_value = [json.dumps({"status": "ok", "fee_cents": 2500})]
    process.wait.return_value = 0
    sandbox.exec.return_value = process
    if failure:
        sandbox.exec.side_effect = RuntimeError("synthetic-secret-provider-error")
    config = Settings(
        _env_file=None,
        allow_billable_modal=True,
        modal_token_id="synthetic-id",
        modal_token_secret="synthetic-secret",
    )
    result = ModalExecutor(config, sdk).run(
        "java",
        "// reviewed synthetic code",
        TestCase(id="one", due_date="2026-10-30", payment_date="2026-11-05"),
    )
    assert result.status == ("error" if failure else "ok")
    assert "synthetic-secret" not in result.model_dump_json()
    args = sdk.Sandbox.create.call_args.kwargs
    assert args["block_network"] is True and args["timeout"] == 30
    assert args["memory"] == (128, 512) and args["cpu"] == (0.25, 1.0)
    assert args["secrets"] == [] and args["env"] == {}
    assert args["include_oidc_identity_token"] is False
    sandbox.terminate.assert_called_once()


def test_installed_sdk_supports_required_filesystem():
    import modal
    from modal.sandbox._filesystem import _SandboxFilesystem

    assert callable(modal.Client.from_credentials)
    assert callable(_SandboxFilesystem.write_text)


def execution_fixture():
    sdk = MagicMock()
    sandbox = sdk.Sandbox.create.return_value
    process = sandbox.exec.return_value
    process.stdout.__iter__.return_value = ['{"status":"ok","fee_cents":0}']
    process.wait.return_value = 0
    config = Settings(
        _env_file=None,
        allow_billable_modal=True,
        modal_token_id="synthetic-id",
        modal_token_secret="synthetic-secret",
    )
    case = TestCase(id="one", due_date="2026-11-01", payment_date="2026-11-01")
    return ModalExecutor(config, sdk), sandbox, process, case


@pytest.mark.parametrize("error_class", [TimeoutError, ExecTimeoutError, SandboxTimeoutError])
def test_actual_sdk_timeout_types_are_preserved(error_class):
    executor, sandbox, _, case = execution_fixture()
    sandbox.exec.side_effect = error_class("synthetic-sensitive-provider-detail")
    result = executor.run("python", "print(0)", case)
    assert result.status == "timeout"
    assert result.fee_cents is None
    assert "synthetic-sensitive" not in result.model_dump_json()
    sandbox.terminate.assert_called_once()


def test_modal_wait_timeout_sentinel_is_preserved():
    executor, sandbox, process, case = execution_fixture()
    process.wait.return_value = -1
    result = executor.run("python", "print(0)", case)
    assert result.status == "timeout"
    assert result.fee_cents is None
    sandbox.terminate.assert_called_once()


def test_output_overflow_stops_reading_and_terminates():
    executor, sandbox, process, case = execution_fixture()
    process.stdout.__iter__.return_value = ["x" * 4097]
    result = executor.run("python", "print(0)", case)
    assert result.status == "error" and result.fee_cents is None
    assert result.error == "Sandbox output exceeded 4 KB."
    process.wait.assert_not_called()
    sandbox.terminate.assert_called_once()


def test_malformed_json_fails_safely_and_terminates():
    executor, sandbox, process, case = execution_fixture()
    process.stdout.__iter__.return_value = ["synthetic-sensitive-stdout"]
    result = executor.run("python", "print(0)", case)
    assert result.status == "error" and result.fee_cents is None
    assert "synthetic-sensitive" not in result.model_dump_json()
    sandbox.terminate.assert_called_once()


def test_fresh_sandbox_per_call_and_no_mounts():
    executor, sandbox, process, case = execution_fixture()
    # Set a new iterable on each mocked exec; no source is executed locally.
    for _ in range(2):
        process.stdout.__iter__.return_value = ['{"status":"error","error":"private-remote-data"}']
        result = executor.run("python", "# network attempt is untrusted source data", case)
        assert result.status == "error" and "private-remote-data" not in result.error
    assert executor.sdk.Sandbox.create.call_count == 2
    args = executor.sdk.Sandbox.create.call_args.kwargs
    assert args["volumes"] == args["network_file_systems"] == {}
    assert args["block_network"] is True
    assert sandbox.terminate.call_count == 2


def test_remote_unicode_output_is_bounded_in_bytes():
    executor, sandbox, process, case = execution_fixture()
    process.stdout.__iter__.return_value = ["界" * 1400]
    assert executor.run("python", "print(0)", case).status == "error"
    process.wait.assert_not_called()
    sandbox.terminate.assert_called_once()


def test_cleanup_failure_is_logged_without_provider_details(caplog):
    executor, sandbox, _, case = execution_fixture()
    sandbox.terminate.side_effect = RuntimeError("private-provider-data")
    assert executor.run("python", "print(0)", case).status == "ok"
    assert "sandbox_cleanup_failed" in caplog.text
    assert "private-provider-data" not in caplog.text
