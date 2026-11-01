from rulereplay.domain import ExecutionResult, OracleResult, Verdict

CLASSIFIER_VERSION = "late-fee-classifier-v1"


def classify(
    oracle: OracleResult, legacy: ExecutionResult, updated: ExecutionResult
) -> tuple[Verdict, str]:
    if legacy.status != "ok" or updated.status != "ok":
        return Verdict.EXECUTION_FAILURE, "At least one implementation did not return a valid fee."
    if not oracle.supported:
        return Verdict.INSUFFICIENT, "No approved policy evidence supports a compliance verdict."
    old_ok = legacy.fee_cents == oracle.fee_cents
    new_ok = updated.fee_cents == oracle.fee_cents
    if old_ok and new_ok:
        return Verdict.COMPLIANT, "Both implementations agree with the applicable approved policy."
    if old_ok:
        return (
            Verdict.REGRESSION,
            "Legacy follows the approved policy; updated behavior violates it.",
        )
    if not new_ok:
        return Verdict.BOTH_WRONG, "Neither implementation matches the approved policy oracle."
    if (
        oracle.predecessor_policy_id
        and legacy.fee_cents == oracle.predecessor_fee_cents
        and oracle.predecessor_fee_cents != oracle.fee_cents
    ):
        return Verdict.AUTHORIZED, (
            "Updated behavior follows the new approved rule; legacy matches its documented "
            "predecessor. The difference is an authorized policy change."
        )
    return Verdict.CORRECTED, "Updated behavior matches policy and corrects a legacy defect."
