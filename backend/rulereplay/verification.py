import platform
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from rulereplay.classify import CLASSIFIER_VERSION, classify
from rulereplay.config import ConfigurationError, Settings
from rulereplay.contracts import EvidenceRepository, ExecutionGateway
from rulereplay.domain import Finding, PolicySet, StrictModel, TestCase, Verdict
from rulereplay.evidence import validate_context
from rulereplay.execution import ModalExecutor
from rulereplay.fixtures import fixture_sources, source_hash
from rulereplay.generation import offline_cases
from rulereplay.integrity import digest
from rulereplay.lifecycle import RunTrace, event
from rulereplay.oracle import ORACLE_VERSION, evaluate
from rulereplay.simulator import Scenario, simulate
from rulereplay.storage import RecordError


class VerifyRequest(StrictModel):
    scenario: Scenario = "payment_date_bug"
    mode: Literal["simulator", "modal"] = "simulator"
    cases: list[dict] | None = Field(default=None, min_length=1, max_length=48)
    generation_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    java_source: str | None = Field(default=None, min_length=1, max_length=50000)
    python_source: str | None = Field(default=None, min_length=1, max_length=50000)

    @model_validator(mode="after")
    def safe_execution(self):
        if (self.java_source is None) != (self.python_source is None):
            raise ValueError("Supply both Java and Python source together")
        if self.java_source is not None and self.mode != "modal":
            raise ValueError("Submitted source can run only in Modal Sandboxes")
        if self.cases is not None and self.generation_id is not None:
            raise ValueError("Use either explicit cases or a saved generated suite")
        return self


def summarize(findings: list[Finding]) -> dict:
    counts = {v.value: 0 for v in Verdict}
    counts.update(Counter(f.verdict.value for f in findings))
    blockers = sum(
        counts[v.value] for v in (Verdict.REGRESSION, Verdict.BOTH_WRONG, Verdict.EXECUTION_FAILURE)
    )
    unresolved = counts[Verdict.INSUFFICIENT] + counts[Verdict.INVALID]
    return {
        "total": len(findings),
        "counts": counts,
        "blockers": blockers,
        "unresolved": unresolved,
        "decision": "hold" if blockers else "review" if unresolved or not findings else "pass",
        "scope": "Decision applies only to the supplied cases and policy evidence; not a proof "
        "of complete correctness or regulatory compliance.",
    }


def release_outcome(findings: list[Finding], mode: str, rejected_count: int = 0) -> dict:
    """Advisory only: fail for observed defects; review gaps; never pass simulation."""
    verdicts = {finding.verdict for finding in findings}
    if verdicts & {Verdict.REGRESSION, Verdict.BOTH_WRONG}:
        outcome = "FAIL"
        reason = "Policy violations detected in the recorded execution mode."
    elif (
        rejected_count
        or not findings
        or verdicts
        & {
            Verdict.INSUFFICIENT,
            Verdict.INVALID,
            Verdict.EXECUTION_FAILURE,
        }
    ):
        outcome = "REVIEW"
        reason = "Required evidence is missing, invalid or execution failed."
    elif mode != "modal":
        outcome = "UNVERIFIED"
        reason = "Simulator observations do not verify submitted implementations."
    else:
        outcome = "PASS"
        reason = "Tested behaviors comply under the available live execution and policy evidence."
    return {
        "outcome": outcome,
        "reason": reason,
        "execution_mode": mode,
        "automatic_approval": False,
    }


def verify(
    request: VerifyRequest,
    settings: Settings,
    policies: PolicySet,
    store: EvidenceRepository,
    generations: EvidenceRepository,
    executor: ExecutionGateway | None = None,
    trace: RunTrace | None = None,
) -> dict:
    trace = trace or RunTrace()
    trace.transition("VALIDATING")
    if request.mode == "modal":
        settings.require_modal()
    sources = (
        fixture_sources(request.scenario)
        if request.java_source is None
        else {"java": request.java_source, "python": request.python_source}
    )
    generation = None
    if request.generation_id:
        generation = generations.get(request.generation_id)
        if generation["source_sha256"] != {k: source_hash(v) for k, v in sources.items()}:
            raise RecordError("Source changed since generation. Generate a fresh suite.")
        if generation["suite"]["policy_sha256"] != digest(policies.model_dump(mode="json")):
            raise RecordError("Policy evidence changed since generation. Generate a fresh suite.")
        raw_cases = generation["suite"]["cases"]
    elif request.cases is not None:
        raw_cases = request.cases
    else:
        raw_cases = [c.model_dump(mode="json") for c in offline_cases(policies).cases]
    if len(raw_cases) > settings.max_tests_per_analysis:
        raise ConfigurationError("Analysis exceeds the configured test budget.")
    if request.mode == "modal" and len(raw_cases) * 2 > settings.max_sandboxes_per_analysis:
        raise ConfigurationError("Modal runs are limited to 16 cases (32 isolated executions).")
    validated, seen, ids = [], set(), set()
    sandbox_calls = 0
    duplicates = 0
    for index, raw in enumerate(raw_cases):
        try:
            case = TestCase.model_validate(raw)
            if case.id in ids and case.key not in seen:
                raise ValueError("Duplicate case identifier")
        except (ValidationError, ValueError):
            validated.append(
                Finding(
                    # ':' cannot occur in a validated TestCase ID, so these internal
                    # identifiers cannot collide with valid cases earlier or later in the suite.
                    case_id=f"invalid:{index + 1}",
                    case=None,
                    oracle=None,
                    legacy=None,
                    updated=None,
                    verdict=Verdict.INVALID,
                    reason="Input requires a unique ID and valid YYYY-MM-DD dates; "
                    "unknown fields and ambiguous IDs are rejected.",
                )
            )
            continue
        if case.key in seen:
            duplicates += 1
            continue
        seen.add(case.key)
        ids.add(case.id)
        validated.append(case)
    trace.transition("EXECUTING")
    observations = []
    for item in validated:
        if isinstance(item, Finding):
            observations.append(item)
            continue
        case = item
        if request.mode == "simulator":
            legacy, updated = simulate(case, request.scenario)
        else:
            runner = executor or ModalExecutor(settings)
            sandbox_calls += 2
            legacy = runner.run("java", sources["java"], case)
            updated = runner.run("python", sources["python"], case)
        observations.append((case, legacy, updated))
    trace.transition("EVALUATING")
    findings = []
    for item in observations:
        if isinstance(item, Finding):
            findings.append(item)
            continue
        case, legacy, updated = item
        oracle = evaluate(case, policies)
        verdict, reason = classify(oracle, legacy, updated)
        findings.append(
            Finding(
                case_id=case.id,
                case=case,
                oracle=oracle,
                legacy=legacy,
                updated=updated,
                verdict=verdict,
                reason=reason,
            )
        )
    release = release_outcome(
        findings, request.mode, generation["suite"].get("rejected_count", 0) if generation else 0
    )

    event(
        "analysis_evaluated",
        trace.id,
        counts=summarize(findings)["counts"],
        sandbox_executions=sandbox_calls,
        rejected=summarize(findings)["counts"]["invalid_input"],
    )
    needs_review = (
        release["outcome"] in {"REVIEW", "UNVERIFIED"}
        or any(
            f.verdict in {Verdict.INSUFFICIENT, Verdict.INVALID, Verdict.EXECUTION_FAILURE}
            for f in findings
        )
        or bool(generation and generation["suite"].get("rejected_count", 0))
    )
    return trace.persist(
        store,
        {
            "correlation_id": trace.id,
            "release": release,
            "metrics": {
                "sandbox_executions": sandbox_calls,
                "model_calls": 0,
                "duration_ms": trace.history[-1]["elapsed_ms"],
            },
            "runtime": {
                "python": platform.python_version(),
                "application": "0.1.0",
                "harness_sha256": source_hash(
                    Path(__file__).with_name("sandbox_runner.py").read_text()
                ),
            },
            "test_source": generation["suite"]["source"]
            if generation
            else ("explicit_inputs" if request.cases is not None else "offline_boundary"),
            "created_at": datetime.now(UTC).isoformat(),
            "scenario": request.scenario,
            "execution_mode": request.mode,
            "oracle_version": ORACLE_VERSION,
            "classifier_version": CLASSIFIER_VERSION,
            "generation": generation,
            "policies": policies.model_dump(mode="json"),
            "policy_sha256": digest(policies.model_dump(mode="json")),
            "sources": sources,
            "source_sha256": {key: source_hash(source) for key, source in sources.items()},
            "findings": [f.model_dump(mode="json") for f in findings],
            "summary": summarize(findings),
            "duplicates_removed": duplicates,
            "execution_note": "Trusted fixture simulation; not a Modal execution."
            if request.mode == "simulator"
            else "Java and Python executed in separate Modal Sandboxes.",
        },
        "NEEDS_REVIEW" if needs_review else "COMPLETED",
    )


def replay(record: dict) -> dict:
    if record.get("classifier_version", CLASSIFIER_VERSION) != CLASSIFIER_VERSION:
        raise RecordError("The saved classifier version is not supported by this build.")
    if record["oracle_version"] != ORACLE_VERSION:
        raise RecordError("The saved oracle version is not supported by this build.")
    try:
        policies, findings = validate_context(record)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise RecordError("Saved evidence context is incomplete or inconsistent.") from None
    mismatches = []
    for finding in findings:
        if finding.case is None:
            continue
        expected = evaluate(finding.case, policies)
        verdict, reason = classify(expected, finding.legacy, finding.updated)
        if expected != finding.oracle or verdict != finding.verdict or reason != finding.reason:
            mismatches.append(finding.case_id)
    consistent = not mismatches and summarize(findings) == record["summary"]
    if "release" in record:
        consistent = consistent and record["release"] == release_outcome(
            findings,
            record["execution_mode"],
            record["generation"]["suite"].get("rejected_count", 0)
            if record.get("generation")
            else 0,
        )
    event("evidence_replay", record.get("correlation_id", record["id"]), consistent=consistent)
    return {
        "context_differences": [
            key
            for key, current in {
                "python": platform.python_version(),
                "harness_sha256": source_hash(
                    Path(__file__).with_name("sandbox_runner.py").read_text()
                ),
            }.items()
            if record.get("runtime", {}).get(key) not in {None, current}
        ],
        "outcome": "CONSISTENT" if consistent else "REPLAY_MISMATCH",
        "run_id": record["id"],
        "consistent": consistent,
        "mismatches": mismatches,
        "mode": "evidence_replay",
        "note": "Recomputed oracle and classifications from "
        "saved policies and execution observations. No source execution or cloud call.",
        "summary": summarize(findings),
    }
