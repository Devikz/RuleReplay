"""Check Git exclusion and known local secrets without ever printing their values."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    forbidden = [
        p for p in tracked if Path(p).name.startswith(".env") and Path(p).name != ".env.example"
    ]
    if forbidden:
        raise SystemExit("FAIL: a private environment file is tracked.")
    if subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT).returncode != 0:
        raise SystemExit("FAIL: .env is not ignored.")
    if subprocess.run(["git", "check-ignore", "-q", ".env.example"], cwd=ROOT).returncode == 0:
        raise SystemExit("FAIL: .env.example must be trackable.")
    files = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    env = ROOT / ".env"
    secrets = []
    if env.exists():
        for key, value in re.findall(
            r"^[ \t]*(\w+)[ \t]*=[ \t]*(.*?)[ \t]*$", env.read_text(), re.M
        ):
            if key in {"MODEL_API_KEY", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"}:
                value = value.strip("\"'")
                if len(value) >= 8 and not value.startswith("<") and value != "placeholder":
                    secrets.append(value.encode())
    candidates = [ROOT / name for name in files if name]
    candidates += list((ROOT / "frontend/dist").rglob("*"))
    patterns = [
        rb"gh[pousr]_[A-Za-z0-9]{30,}",
        rb"AKIA[0-9A-Z]{16}",
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ]
    for path in candidates:
        if path.is_file() and not path.is_symlink():
            content = path.read_bytes()
            if any(re.search(pattern, content) for pattern in patterns):
                raise SystemExit("FAIL: a credential-like pattern occurs in a publishable file.")
            if path.name == ".env.example" and re.search(
                rb"(?m)^(?:MODEL_API_KEY|MODAL_TOKEN_ID|MODAL_TOKEN_SECRET)=[^\r\n\s]+", content
            ):
                raise SystemExit("FAIL: example credentials must be empty.")
            if any(secret in content for secret in secrets):
                raise SystemExit("FAIL: a local credential occurs in a publishable file or bundle.")
    print(
        "PASS: private environment files untracked and ignored; "
        "no known local secrets in source/bundle."
    )


if __name__ == "__main__":
    main()
