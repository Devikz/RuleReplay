"""Independent oracle: no implementation fixtures or model output are imported here."""

from rulereplay.domain import OracleResult, PolicySet, TestCase

ORACLE_VERSION = "late-fee-calendar-v1"


def evaluate(case: TestCase, policy_set: PolicySet) -> OracleResult:
    days_late = max(0, (case.payment_date - case.due_date).days)
    candidates = [
        p
        for p in policy_set.policies
        if p.status == "approved"
        and p.effective_from <= case.due_date
        and (p.effective_until is None or case.due_date < p.effective_until)
    ]
    if len(candidates) != 1:
        return OracleResult(
            supported=False,
            fee_cents=None,
            policy_id=None,
            days_late=days_late,
            grace_days=None,
            explanation="No unique approved policy covers this loan due date.",
        )
    policy = candidates[0]
    exceeds = days_late > policy.grace_days
    fee = policy.fee_cents if exceeds else 0
    predecessor = next((p for p in policy_set.policies if p.id == policy.supersedes), None)
    return OracleResult(
        supported=True,
        fee_cents=fee,
        policy_id=policy.id,
        days_late=days_late,
        grace_days=policy.grace_days,
        explanation=(
            f"Due date {case.due_date} selects {policy.id}. "
            f"{days_late} calendar days late {'exceeds' if exceeds else 'does not exceed'} "
            f"the {policy.grace_days}-day grace period; fee = {fee} USD cents."
        ),
        predecessor_policy_id=predecessor.id if predecessor else None,
        predecessor_fee_cents=(predecessor.fee_cents if days_late > predecessor.grace_days else 0)
        if predecessor
        else None,
    )
