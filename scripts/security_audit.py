"""Query vulnerability feeds. Findings fail; unavailable feeds are explicitly unverified."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def classify(tool, code, output):
    try:
        data = json.loads(output)
        if tool == "python":
            dependencies = data["dependencies"]
            findings = [
                {"package": dep["name"], "id": item["id"]}
                for dep in dependencies
                for item in dep.get("vulns", [])
            ]
            incomplete = any("skip_reason" in dep for dep in dependencies)
        else:
            findings = [
                {"package": name, "severity": item["severity"]}
                for name, item in data["vulnerabilities"].items()
            ]
            incomplete = False
        status = (
            "FINDINGS" if findings else "PASS" if code == 0 and not incomplete else "UNAVAILABLE"
        )
        return {"tool": tool, "status": status, "findings": findings}
    except (ValueError, KeyError, TypeError):
        return {"tool": tool, "status": "UNAVAILABLE", "findings": []}


def query(tool, args):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=90)
        return classify(tool, result.returncode, result.stdout)
    except (OSError, subprocess.TimeoutExpired):
        return {"tool": tool, "status": "UNAVAILABLE", "findings": []}


def main():
    with tempfile.TemporaryDirectory(prefix="rulereplay-audit-") as directory:
        requirements = Path(directory) / "requirements.txt"
        exported = subprocess.run(
            [
                "uv",
                "export",
                "--frozen",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ],
            cwd=ROOT,
            capture_output=True,
            timeout=60,
        )
        if exported.returncode:
            raise SystemExit("Locked dependency export failed; fix the lockfile/tool installation.")
        results = [
            query(
                "python",
                [
                    sys.executable,
                    "-m",
                    "pip_audit",
                    "-r",
                    str(requirements),
                    "--no-deps",
                    "--disable-pip",
                    "--format",
                    "json",
                    "--progress-spinner",
                    "off",
                    "--timeout",
                    "10",
                    "--cache-dir",
                    str(Path(directory) / "cache"),
                ],
            ),
            query("npm", ["npm", "--prefix", "frontend", "audit", "--json"]),
        ]
    output = ROOT / ".local/security"
    output.mkdir(parents=True, exist_ok=True)
    (output / "dependency-audit.json").write_text(json.dumps(results, indent=2) + "\n")
    for result in results:
        print(f"{result['tool']}: {result['status']} ({len(result['findings'])} findings)")
        if result["status"] == "UNAVAILABLE":
            print(
                "::warning::Dependency audit unavailable/incomplete; security status is UNVERIFIED."
            )
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(
                "\nDependency audits: "
                + ", ".join(f"{result['tool']} **{result['status']}**" for result in results)
                + "\n"
            )
    return int(any(result["status"] == "FINDINGS" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
