"""Bounded, domain-specific shrinking. Not a general ddmin implementation."""

from datetime import timedelta

from rulereplay.classify import classify
from rulereplay.domain import PolicySet, TestCase, Verdict
from rulereplay.oracle import evaluate
from rulereplay.simulator import simulate
from rulereplay.storage import RecordError


def minimize(record: dict, case_id: str) -> dict:
    if record["execution_mode"] != "simulator":
        raise RecordError("Offline shrinking supports trusted fixture simulations only.")
    finding = next((f for f in record["findings"] if f["case_id"] == case_id), None)
    if not finding or finding["verdict"] not in {Verdict.REGRESSION, Verdict.BOTH_WRONG}:
        raise RecordError("Select a regression or both-wrong finding to minimize.")
    original = TestCase.model_validate(finding["case"])
    policies = PolicySet.model_validate(record["policies"])
    checked = 0
    for delay in range(min(max(0, (original.payment_date - original.due_date).days), 90) + 1):
        candidate = original.model_copy(
            update={"payment_date": original.due_date + timedelta(days=delay)}
        )
        oracle = evaluate(candidate, policies)
        legacy, updated = simulate(candidate, record["scenario"])
        checked += 1
        verdict, _ = classify(oracle, legacy, updated)
        if verdict == finding["verdict"]:
            return {
                "case": candidate.model_dump(mode="json"),
                "verdict": verdict,
                "checked": checked,
                "expected_cents": oracle.fee_cents,
                "note": "Smallest nonnegative delay at the original due date preserving this "
                "verdict, within a 90-day search. No cloud call or submitted-code execution.",
            }
    raise RecordError("No smaller counterexample was found within the bounded search.")
