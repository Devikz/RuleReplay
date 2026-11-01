from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from rulereplay.classify import classify
from rulereplay.domain import ExecutionResult, PolicySet, TestCase, Verdict
from rulereplay.oracle import evaluate
from rulereplay.policies import load_policies
from rulereplay.simulator import simulate


def case(due, paid):
    return TestCase(id="case", due_date=due, payment_date=paid)


@pytest.mark.parametrize(
    "due,paid,expected,policy",
    [
        ("2026-10-25", "2026-10-30", 0, "LATE-FEE-V1"),
        ("2026-10-25", "2026-10-31", 2500, "LATE-FEE-V1"),
        ("2026-10-30", "2026-11-05", 2500, "LATE-FEE-V1"),
        ("2026-11-01", "2026-11-08", 0, "LATE-FEE-V2"),
        ("2026-11-01", "2026-11-09", 2500, "LATE-FEE-V2"),
        ("2026-11-01", "2026-10-30", 0, "LATE-FEE-V2"),
        ("2028-02-28", "2028-03-06", 0, "LATE-FEE-V2"),
    ],
)
def test_oracle_boundaries(due, paid, expected, policy):
    result = evaluate(case(due, paid), load_policies())
    assert (result.fee_cents, result.policy_id) == (expected, policy)


@pytest.mark.parametrize(
    "scenario,due,paid,verdict",
    [
        ("payment_date_bug", "2026-10-30", "2026-11-05", Verdict.REGRESSION),
        ("payment_date_bug", "2026-11-01", "2026-11-07", Verdict.AUTHORIZED),
        ("legacy_defect", "2026-10-01", "2026-10-06", Verdict.CORRECTED),
        ("both_wrong", "2026-10-01", "2026-10-09", Verdict.BOTH_WRONG),
        ("payment_date_bug", "2025-12-20", "2025-12-28", Verdict.INSUFFICIENT),
        ("payment_date_bug", "2026-10-01", "2026-10-03", Verdict.COMPLIANT),
        ("execution_error", "2026-10-01", "2026-10-03", Verdict.EXECUTION_FAILURE),
    ],
)
def test_classification(scenario, due, paid, verdict):
    test_case = case(due, paid)
    assert (
        classify(evaluate(test_case, load_policies()), *simulate(test_case, scenario))[0] == verdict
    )


def test_new_correct_does_not_imply_authorized_change():
    oracle = evaluate(case("2026-11-01", "2026-11-07"), load_policies())
    wrong = ExecutionResult(status="ok", fee_cents=1700)
    right = ExecutionResult(status="ok", fee_cents=0)
    assert classify(oracle, wrong, right)[0] == Verdict.CORRECTED


def test_reject_ambiguous_policy_overlap():
    data = load_policies().model_dump(mode="json")
    data["policies"][0]["effective_until"] = "2026-11-02"
    with pytest.raises(ValidationError, match="overlap"):
        PolicySet.model_validate(data)


def test_draft_policy_is_not_evidence():
    data = load_policies().model_dump(mode="json")
    data["policies"][1]["status"] = "draft"
    result = evaluate(case("2026-11-01", "2026-11-10"), PolicySet.model_validate(data))
    assert not result.supported


@pytest.mark.parametrize("invalid", ["2026-02-30", "2026-11-01T12:00:00Z", 1793491200, True])
def test_invalid_dates(invalid):
    with pytest.raises(ValidationError):
        case(invalid, "2026-11-09")


@given(st.integers(min_value=-30, max_value=90))
def test_fee_monotonicity_and_single_fee(delay):
    policies = load_policies()
    due = date(2026, 11, 1)
    first = evaluate(case(due, due + timedelta(days=delay)), policies).fee_cents
    later = evaluate(case(due, due + timedelta(days=delay + 1)), policies).fee_cents
    assert first in (0, 2500)
    assert first <= later


@pytest.mark.parametrize("value", ["2026-W45-1", "0001-01-01", "9999-12-31", 1793491200, True])
def test_date_contract_applies_to_policy_and_approval(value):
    for field in ("effective_from", "effective_until", "approved_on"):
        data = load_policies().model_dump(mode="json")
        target = data["policies"][0]
        if field == "approved_on":
            target["provenance"][field] = value
        else:
            target[field] = value
        with pytest.raises(ValidationError):
            PolicySet.model_validate(data)


def test_iso_week_input_is_not_a_calendar_date():
    with pytest.raises(ValidationError):
        case("2026-W45-1", "2026-11-09")


@pytest.mark.parametrize("field", ["document", "clause", "approved_by", "change_reason"])
def test_approved_policy_requires_nonblank_provenance(field):
    data = load_policies().model_dump(mode="json")
    data["policies"][0]["provenance"][field] = "   \t\n"
    with pytest.raises(ValidationError):
        PolicySet.model_validate(data)
