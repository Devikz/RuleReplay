"""Explicit local simulation of reviewed fixture behaviors. NEVER evaluates submitted source.

This module is separate from the oracle, and returns observations, not expected values.
Actual cross-language execution is handled by Modal, or fixed repository tests only.
"""

from datetime import date
from typing import Literal

from rulereplay.domain import ExecutionResult, TestCase

Scenario = Literal[
    "payment_date_bug", "corrected", "legacy_defect", "both_wrong", "execution_error"
]
SCENARIOS = {
    "payment_date_bug": "Payment-date policy bug",
    "corrected": "Corrected update",
    "legacy_defect": "Legacy threshold defect corrected",
    "both_wrong": "Both implementations charge the wrong amount",
    "execution_error": "Updated implementation fails",
}


def simulate(case: TestCase, scenario: Scenario = "payment_date_bug"):
    late = (case.payment_date - case.due_date).days
    legacy_fee = 2500 if late > 5 else 0
    grace = 7 if case.payment_date >= date(2026, 11, 1) else 5
    updated_fee = 2500 if late > grace else 0
    if scenario in {"corrected", "legacy_defect"}:
        updated_grace = 7 if case.due_date >= date(2026, 11, 1) else 5
        updated_fee = 2500 if late > updated_grace else 0
    if scenario == "legacy_defect":
        legacy_fee = 2500 if late >= 5 else 0
    if scenario == "both_wrong":
        legacy_fee = updated_fee = 3000 if late > 5 else 0
    legacy = ExecutionResult(status="ok", fee_cents=legacy_fee)
    updated = ExecutionResult(status="ok", fee_cents=updated_fee)
    if scenario == "execution_error":
        updated = ExecutionResult(status="error", error="Synthetic execution failure.")
    return legacy, updated
