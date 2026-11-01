"""Exercise harness failure handling using fake processes; never run submitted code locally."""

import json
import subprocess
from unittest.mock import MagicMock

import pytest
from rulereplay import sandbox_runner as runner


@pytest.mark.parametrize(
    "status,output,expected",
    [
        ("ok", "2500", "ok"),
        ("ok", "25.00", "error"),
        ("ok", "True", "error"),
        ("ok", "0\n2500", "error"),
        ("ok", "1000001", "error"),
        ("ok", "-1", "error"),
        ("timeout", "", "timeout"),
        ("error", "", "error"),
    ],
)
def test_harness_validates_output(monkeypatch, capsys, status, output, expected):
    monkeypatch.setattr(runner.sys, "argv", ["runner.py", "python", "2026-10-30", "2026-11-05"])
    monkeypatch.setattr(runner, "command", lambda *args: (status, output))
    runner.main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == expected
    if expected != "ok":
        assert "fee_cents" not in result


def test_java_compilation_failure(monkeypatch, capsys):
    monkeypatch.setattr(runner.sys, "argv", ["runner.py", "java", "2026-10-30", "2026-11-05"])
    monkeypatch.setattr(runner, "command", lambda *args: ("error", "private compiler output"))
    runner.main()
    assert json.loads(capsys.readouterr().out)["error"] == "Java compilation failed or timed out."


def test_harness_timeout_kills_process_group(monkeypatch):
    child = MagicMock(pid=123, returncode=-9)
    child.wait.side_effect = [subprocess.TimeoutExpired("synthetic", 3), None]
    popen = MagicMock(return_value=child)
    kill = MagicMock()
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    monkeypatch.setattr(runner.os, "killpg", kill)
    assert runner.command(["synthetic-never-executed"], 3) == ("timeout", "")
    assert kill.call_count >= 1
    assert popen.call_args.kwargs["env"] == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/tmp",
        "LANG": "C.UTF-8",
    }
    assert popen.call_args.kwargs["start_new_session"]


def test_harness_resource_caps(monkeypatch):
    setter = MagicMock()
    monkeypatch.setattr(runner.resource, "setrlimit", setter)
    runner.limits()
    assert setter.call_count == 5


@pytest.mark.parametrize(
    "output,expected_status",
    [
        (b"2500\n", "ok"),
        (b"0" + b" " * 255, "ok"),
        (b"0" + b" " * 255 + b"\n2500", "error"),
        (b"0" + b" " * 16383, "error"),
    ],
)
def test_complete_stdout_must_fit_parsing_budget(monkeypatch, output, expected_status):
    # Fake Popen writes observations into the capture file; no subprocess/source is executed.
    child = MagicMock(pid=123, returncode=0)

    def fake_process(*args, **kwargs):
        kwargs["stdout"].write(output)
        return child

    monkeypatch.setattr(runner.subprocess, "Popen", fake_process)
    monkeypatch.setattr(runner.os, "killpg", MagicMock())
    status, captured = runner.command(["synthetic-never-executed"], 3)
    assert status == expected_status
    if expected_status == "error":
        assert captured == ""
