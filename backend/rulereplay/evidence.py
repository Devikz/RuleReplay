"""Validate saved context independently of its outer checksum and of AI output."""

from rulereplay.domain import Finding, PolicySet, Verdict
from rulereplay.fixtures import source_hash
from rulereplay.integrity import digest


def validate_context(record: dict) -> tuple[PolicySet, list[Finding]]:
    policies = PolicySet.model_validate(record["policies"])
    if digest(policies.model_dump(mode="json")) != record["policy_sha256"]:
        raise ValueError("Policy snapshot fingerprint mismatch")
    sources = record["sources"]
    if (
        set(sources) != {"java", "python"}
        or {key: source_hash(value) for key, value in sources.items()} != record["source_sha256"]
    ):
        raise ValueError("Source snapshot fingerprint mismatch")
    if record["execution_mode"] not in {"simulator", "modal"}:
        raise ValueError("Invalid execution mode")
    findings = [Finding.model_validate(f) for f in record["findings"]]
    if not findings or len(findings) > 48:
        raise ValueError("Missing or oversized findings")
    seen_ids, seen_inputs = set(), set()
    for finding in findings:
        if finding.case_id in seen_ids:
            raise ValueError("Duplicate finding")
        seen_ids.add(finding.case_id)
        if finding.case is None:
            if finding.verdict != Verdict.INVALID or any(
                value is not None for value in (finding.oracle, finding.legacy, finding.updated)
            ):
                raise ValueError("Incomplete finding evidence")
        elif (
            finding.case.id != finding.case_id
            or finding.case.key in seen_inputs
            or any(value is None for value in (finding.oracle, finding.legacy, finding.updated))
        ):
            raise ValueError("Incomplete or ambiguous finding evidence")
        else:
            seen_inputs.add(finding.case.key)
    generation = record.get("generation")
    if generation:
        if (
            generation["source_sha256"] != record["source_sha256"]
            or generation["suite"]["policy_sha256"] != record["policy_sha256"]
        ):
            raise ValueError("Generation context mismatch")
        receipt = {key: value for key, value in generation.items() if key != "integrity_sha256"}
        if digest(receipt) != generation["integrity_sha256"]:
            raise ValueError("Generation receipt fingerprint mismatch")
    return policies, findings
