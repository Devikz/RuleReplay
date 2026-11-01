"""Only fixed repository-owned fixture source runs on the host, never submitted code."""

import shutil
import subprocess
import sys

import pytest
from rulereplay.domain import TestCase
from rulereplay.fixtures import fixture_sources
from rulereplay.simulator import simulate


@pytest.mark.parametrize(
    "scenario", ["payment_date_bug", "corrected", "legacy_defect", "both_wrong"]
)
def test_actual_trusted_java_python_match_simulation(tmp_path, scenario):
    assert shutil.which("javac"), "A Java 17+ JDK is required for trusted fixture verification"
    sources = fixture_sources(scenario)
    java_file = tmp_path / "LegacyLoan.java"
    python_file = tmp_path / "loan.py"
    java_file.write_text(sources["java"])
    python_file.write_text(sources["python"])
    subprocess.run(["javac", str(java_file)], check=True, capture_output=True, timeout=20)
    for due, paid in [
        ("2026-10-30", "2026-11-05"),
        ("2026-11-01", "2026-11-07"),
        ("2026-10-01", "2026-10-06"),
        ("2026-11-01", "2026-11-09"),
    ]:
        case = TestCase(id="fixture", due_date=due, payment_date=paid)
        old, new = simulate(case, scenario)
        java = subprocess.run(
            ["java", "-cp", str(tmp_path), "LegacyLoan", due, paid],
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        python = subprocess.run(
            [sys.executable, "-I", str(python_file), due, paid],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        assert int(java.stdout) == old.fee_cents
        assert int(python.stdout) == new.fee_cents
