"""Repeatable setup. Preserves credentials and does not enable paid integrations."""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = ROOT / ".env"
    if env.is_symlink():
        raise SystemExit("Refusing a symlinked .env.")
    if not env.exists():
        descriptor = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as file:
            file.write((ROOT / ".env.example").read_text())
    env.chmod(0o600)
    if not shutil.which("uv") or not shutil.which("npm"):
        raise SystemExit("Setup requires uv and Node.js/npm. Python version is pinned to 3.12.")
    environment = dict(os.environ, UV_CACHE_DIR=str(ROOT / ".uv-cache"))
    subprocess.run(["uv", "sync", "--frozen"], cwd=ROOT, env=environment, check=True)
    subprocess.run(
        ["npm", "ci", "--prefix", "frontend", "--no-audit", "--no-fund"], cwd=ROOT, check=True
    )
    subprocess.run(
        [str(ROOT / ".venv/bin/python"), "scripts/check_secrets.py"], cwd=ROOT, check=True
    )
    print("Setup complete. Paid integrations remain controlled by explicit .env opt-ins.")


if __name__ == "__main__":
    main()
