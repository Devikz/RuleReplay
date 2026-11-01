"""Versioned, repository-owned demonstration fixtures; reading never executes them."""

import hashlib

from rulereplay.config import ROOT
from rulereplay.simulator import Scenario


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def fixture_sources(scenario: Scenario = "payment_date_bug") -> dict[str, str]:
    java = (ROOT / "fixtures/legacy/LegacyLoan.java").read_text()
    python = (ROOT / "fixtures/updated/loan.py").read_text()
    if scenario in {"corrected", "legacy_defect"}:
        python = (ROOT / "fixtures/updated/corrected.py").read_text()
    if scenario == "legacy_defect":
        java = java.replace("late > 5", "late >= 5")
    if scenario == "both_wrong":
        java = java.replace("2500", "3000")
        python = python.replace("grace = 7 if paid >= date(2026, 11, 1) else 5", "grace = 5")
        python = python.replace("2500", "3000")
    if scenario == "execution_error":
        python = "raise RuntimeError('Synthetic execution failure')\n"
    return {"java": java, "python": python}
