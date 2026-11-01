from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st
from pydantic import ValidationError
from rulereplay.domain import OracleResult, PolicySet, TestCase
from rulereplay.oracle import evaluate
from rulereplay.policies import load_policies


@given(
    due=st.dates(min_value=date(2001, 1, 1), max_value=date(2099, 1, 1)),
    delay=st.integers(-100, 100),
    grace=st.integers(0, 60),
    fee=st.integers(0, 100000),
)
@hypothesis_settings(max_examples=300, derandomize=True)
def test_calendar_money_invariants(due, delay, grace, fee):
    raw = load_policies().model_dump(mode="json")
    policy = raw["policies"][0]
    policy.update(
        effective_from="2000-01-01", effective_until=None, grace_days=grace, fee_cents=fee
    )
    policy["provenance"]["approved_on"] = "2000-01-01"
    policies = PolicySet(policies=[policy])
    case = TestCase(id="one", due_date=due, payment_date=due + timedelta(days=delay))
    result = evaluate(case, policies)
    assert result.fee_cents == (fee if delay > grace else 0)
    assert result.days_late == max(0, delay)
    assert evaluate(case.model_copy(update={"id": "irrelevant"}), policies) == result
    assert evaluate(case, policies) == result
    later = case.model_copy(update={"payment_date": case.payment_date + timedelta(days=1)})
    assert evaluate(later, policies).fee_cents >= result.fee_cents


@given(
    boundary=st.dates(min_value=date(2020, 1, 2), max_value=date(2099, 12, 1)),
    gap=st.integers(0, 30),
)
@hypothesis_settings(max_examples=150, derandomize=True)
def test_policy_intervals_and_gaps(boundary, gap):
    raw = load_policies().model_dump(mode="json")
    first, second = raw["policies"]
    first.update(effective_from="2000-01-01", effective_until=boundary.isoformat())
    second.update(effective_from=(boundary + timedelta(days=gap)).isoformat(), supersedes=None)
    for policy in (first, second):
        policy["provenance"]["approved_on"] = "2000-01-01"
    policies = PolicySet.model_validate(raw)
    for due, expected in (
        (boundary - timedelta(days=1), first["id"]),
        (boundary, second["id"] if not gap else None),
        (boundary + timedelta(days=gap), second["id"]),
    ):
        result = evaluate(TestCase(id="case", due_date=due, payment_date=due), policies)
        assert result.policy_id == expected
    second["effective_from"] = (boundary - timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError, match="overlap"):
        PolicySet.model_validate(raw)


def test_zero_fee_explanation_still_describes_expired_grace():
    raw = load_policies().model_dump(mode="json")
    raw["policies"][0]["fee_cents"] = 0
    result = evaluate(
        TestCase(id="zero", due_date="2026-10-01", payment_date="2026-10-10"),
        PolicySet.model_validate(raw),
    )
    assert result.fee_cents == 0 and "9 calendar days late exceeds" in result.explanation


def test_policy_snapshot_is_deeply_immutable():
    policies = load_policies()
    with pytest.raises(ValidationError):
        policies.policies[0].fee_cents = 1
    with pytest.raises(ValidationError):
        policies.policies[0].provenance.clause = "override"
    assert isinstance(policies.policies, tuple)


def test_supported_oracle_cannot_omit_evidence():
    with pytest.raises(ValidationError):
        OracleResult(
            supported=True,
            fee_cents=None,
            policy_id=None,
            days_late=0,
            grace_days=None,
            explanation="approve",
        )
