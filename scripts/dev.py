"""Start both local services, and shut down both on Ctrl-C. Never starts cloud work."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    children = []

    def stop(_signal=None, _frame=None):
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(
            subprocess.Popen(
                [
                    str(ROOT / ".venv/bin/python"),
                    "-m",
                    "uvicorn",
                    "rulereplay.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                cwd=ROOT,
                start_new_session=True,
            )
        )
        children.append(
            subprocess.Popen(
                ["npm", "--prefix", "frontend", "run", "dev"],
                cwd=ROOT,
                start_new_session=True,
            )
        )
        print(
            "RuleReplay: http://127.0.0.1:5173 · API docs: http://127.0.0.1:8000/docs", flush=True
        )
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
    finally:
        stop()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
    return max((max(child.returncode or 0, 0) for child in children), default=0)


if __name__ == "__main__":
    sys.exit(main())
