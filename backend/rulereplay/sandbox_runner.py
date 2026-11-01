"""Trusted harness sent to Modal. This file never executes submitted code on the host."""

import json
import os
import re
import resource
import signal

# remote-only trusted supervisor
import subprocess  # nosec B404
import sys
import tempfile
import time
from pathlib import Path


def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (16384, 16384))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


def child_identity():
    """Supervisor stays root inside the sandbox; submitted code runs as nobody."""
    limits()
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)


def command(args, timeout):
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        # fixed argv, remote unprivileged child
        child = subprocess.Popen(  # nosec B603
            args,
            # fixed path in a fresh remote sandbox
            cwd="/tmp/work",  # nosec B108
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
            preexec_fn=child_identity,
            # fixed path in a fresh remote sandbox
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"},  # nosec B108
        )
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            return "timeout", ""
        finally:
            # Kill surviving descendants even when the direct process exits successfully.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        stdout.seek(0)
        # A valid prefix must never hide trailing output beyond the parsing budget.
        raw_output = stdout.read(257)
        if len(raw_output) > 256:
            return "error", ""
        output = raw_output.decode("utf-8", errors="replace").strip()
        return ("ok" if child.returncode == 0 else "error"), output


def main():
    language, due, paid = sys.argv[1:]
    started = time.perf_counter()
    if language == "java":
        status, _ = command(["javac", "-J-Xmx128m", "-proc:none", "LegacyLoan.java"], 10)
        if status != "ok":
            print(json.dumps({"status": status, "error": "Java compilation failed or timed out."}))
            return
        args = [
            "java",
            "-Xmx128m",
            "-XX:ActiveProcessorCount=1",
            "-cp",
            # fixed path in a fresh remote sandbox
            "/tmp/work",  # nosec B108
            "LegacyLoan",
            due,
            paid,
        ]
    else:
        # fixed path in a fresh remote sandbox
        args = ["python", "-I", "/tmp/work/loan.py", due, paid]  # nosec B108
    status, output = command(args, 3)
    result = {"status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 3)}
    if status == "ok" and re.fullmatch(r"(?:0|[1-9][0-9]{0,6})", output) and int(output) <= 1000000:
        result["fee_cents"] = int(output)
    else:
        result["status"] = "timeout" if status == "timeout" else "error"
        result["error"] = (
            "Execution timed out."
            if status == "timeout"
            else ("Execution failed or did not return a single bounded integer fee in cents.")
        )
    print(json.dumps(result))


if __name__ == "__main__":
    # fixed path in a fresh remote sandbox
    if not Path("/tmp/work").is_dir():  # nosec B108
        raise SystemExit("This harness is for Modal Sandboxes only.")
    # fixed path in a fresh remote sandbox
    os.chown("/tmp/work", 65534, 65534)  # nosec B108
    # fixed path in a fresh remote sandbox
    os.chmod("/tmp/work", 0o700)  # nosec B108
    main()
