"""Measured synthetic mutation benchmark. Never substitutes offline results for AI results."""

import argparse
import json
import platform
import random
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from rulereplay.classify import classify
from rulereplay.config import ROOT, Settings, get_settings
from rulereplay.domain import ExecutionResult, TestCase, Verdict
from rulereplay.fixtures import fixture_sources, source_hash
from rulereplay.generation import GenerationRequest, generate_meta, offline_cases
from rulereplay.oracle import evaluate
from rulereplay.policies import load_policies
from rulereplay.storage import Store
from rulereplay.verification import VerifyRequest, replay, verify

SEED = 20261029
BUDGET = 48
DEFECTS = {
    "D01": "Select policy by payment date instead of due date",
    "D02": "Charge on the exact grace day (inclusive threshold)",
    "D03": "Keep the five-day V1 grace period forever",
    "D04": "Apply seven-day grace retroactively to all due dates",
    "D05": "Apply V2 only after, not on, its effective date",
    "D06": "Subtract day-of-month values instead of calendar dates",
    "D07": "Reverse payment and due dates in lateness calculation",
    "D08": "Charge USD 25 per late day instead of a single fee",
    "D09": "Charge USD 30 instead of USD 25",
    "D10": "Drop leap days from elapsed-calendar-day calculation",
}


def observed(case: TestCase, defect: str | None) -> int:
    """Reviewed mutant functions; no oracle imports or generated-source execution here."""
    transition = date(2026, 11, 1)
    grace = 7 if case.due_date >= transition else 5
    late = (case.payment_date - case.due_date).days
    if defect == "D01":
        grace = 7 if case.payment_date >= transition else 5
    if defect == "D02":
        return 2500 if late >= grace else 0
    if defect == "D03":
        grace = 5
    if defect == "D04":
        grace = 7
    if defect == "D05":
        grace = 7 if case.due_date > transition else 5
    if defect == "D06":
        late = case.payment_date.day - case.due_date.day
    if defect == "D07":
        late = -late
    if defect == "D08":
        return 2500 * max(0, late - grace)
    if defect == "D10":
        for year in range(case.due_date.year, case.payment_date.year + 1):
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                if case.due_date <= date(year, 2, 29) < case.payment_date:
                    late -= 1
    amount = 3000 if defect == "D09" else 2500
    return amount if late > grace else 0


def conventional_cases():
    return [
        TestCase(
            id=f"conventional-{day}-{delay}",
            due_date=date(2026, 6, day),
            payment_date=date(2026, 6, day) + timedelta(days=delay),
            rationale="Typical same-month on-time and clearly-late example.",
        )
        for day in range(1, 13)
        for delay in (0, 3, 10, 14)
    ]


def random_cases(seed=SEED):
    # reproducible sampling, not cryptography
    rng = random.Random(seed)  # nosec B311
    cases, keys = [], set()
    while len(cases) < BUDGET:
        due = date(2026, 1, 1) + timedelta(days=rng.randrange(1096))
        paid = due + timedelta(days=rng.randint(-10, 20))
        if (due, paid) not in keys:
            cases.append(
                TestCase(
                    id=f"random-{len(cases) + 1}",
                    due_date=due,
                    payment_date=paid,
                    rationale="Seeded uniform calendar and delay sampling.",
                )
            )
            keys.add((due, paid))
    return cases


def measure(name, cases, policies):
    start = time.perf_counter()
    kills, counterexamples = [], {}
    supported = [(case, evaluate(case, policies)) for case in cases]
    supported = [(case, oracle) for case, oracle in supported if oracle.supported]
    for defect in DEFECTS:
        for case, oracle in supported:
            actual = observed(case, defect)
            if actual != oracle.fee_cents:
                kills.append(defect)
                counterexamples[defect] = {
                    "case": case.model_dump(mode="json"),
                    "expected_cents": oracle.fee_cents,
                    "actual_cents": actual,
                    "policy_id": oracle.policy_id,
                }
                break
    false_alarms = sum(observed(case, None) != oracle.fee_cents for case, oracle in supported)
    boundary_hits = set()
    boundary_targets = set()
    for policy in policies.policies:
        for offset in (-1, 0, 1):
            boundary_targets.add((policy.id, "effective", offset))
            boundary_targets.add((policy.id, "grace", offset))
            for case in cases:
                if case.due_date == policy.effective_from + timedelta(days=offset):
                    boundary_hits.add((policy.id, "effective", offset))
                oracle = evaluate(case, policies)
                if (
                    oracle.policy_id == policy.id
                    and (case.payment_date - case.due_date).days == policy.grace_days + offset
                ):
                    boundary_hits.add((policy.id, "grace", offset))
    authorized_checks = authorized_false_positives = 0
    for case, oracle in supported:
        if oracle.predecessor_policy_id and oracle.predecessor_fee_cents != oracle.fee_cents:
            authorized_checks += 1
            verdict, _ = classify(
                oracle,
                ExecutionResult(status="ok", fee_cents=oracle.predecessor_fee_cents),
                ExecutionResult(status="ok", fee_cents=observed(case, None)),
            )
            authorized_false_positives += int(verdict != Verdict.AUTHORIZED)
    with TemporaryDirectory(prefix="rulereplay-benchmark-") as directory:
        root = Path(directory)
        record = verify(
            VerifyRequest(cases=[case.model_dump(mode="json") for case in cases]),
            Settings(_env_file=None),
            policies,
            Store(root),
            Store(root / "g"),
        )
        replay_consistent = replay(record)["consistent"]
    return {
        "execution_mode": "reviewed_local_mutants",
        "invalid_test_rate": 0.0,
        "execution_failure_rate": 0.0,
        "authorized_change_checks": authorized_checks,
        "authorized_change_false_positives": authorized_false_positives,
        "policy_boundary_hits": len(boundary_hits),
        "policy_boundary_targets": len(boundary_targets),
        "policy_boundary_coverage": len(boundary_hits) / len(boundary_targets),
        "evidence_replay_consistent": replay_consistent,
        "cost_usd": None,
        # unavailable usage metric, not a credential
        "token_usage": None,  # nosec B105
        "method": name,
        "status": "measured locally",
        "cases": len(cases),
        "supported_cases": len(supported),
        "detected": len(kills),
        "total_defects": len(DEFECTS),
        "detection_rate": len(kills) / len(DEFECTS),
        "false_alarms": false_alarms,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
        "killed": kills,
        "counterexamples": counterexamples,
    }


def benchmark(live=False):
    policies = load_policies()
    suites = {
        "Conventional examples": conventional_cases(),
        "Seeded random / oracle property": random_cases(),
        "RuleReplay offline boundaries (ablation)": offline_cases(policies, BUDGET).cases,
    }
    receipts = {}
    rows = [measure(name, cases, policies) for name, cases in suites.items()]
    for contextual, name in (
        (False, "AI tests without policy context"),
        (True, "Full RuleReplay / Muse Wonder"),
    ):
        if live:
            settings = get_settings()
            settings.require_meta()
            suite = generate_meta(
                settings,
                GenerationRequest(mode="meta", count=BUDGET, policy_context=contextual),
                policies,
                fixture_sources(),
            )
            suites[name] = suite.cases
            receipts[name] = suite.model_dump(mode="json")
            measured = measure(name, suite.cases, policies)
            generated_count = len(suite.cases) + suite.rejected_count + suite.duplicate_count
            measured["invalid_test_rate"] = suite.rejected_count / generated_count
            measured["token_usage"] = suite.token_usage
            rows.append(measured)
        else:
            rows.append(
                {
                    "method": name,
                    "status": "not run — paid approval required",
                    "cases": None,
                    "supported_cases": None,
                    "detected": None,
                    "total_defects": len(DEFECTS),
                    "detection_rate": None,
                    "false_alarms": None,
                    "elapsed_ms": None,
                    "killed": [],
                }
            )
    return {
        "status": "measured_local_partial" if not live else "measured_with_live_generation",
        "seed": SEED,
        "case_budget": BUDGET,
        "created_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "execution": "Reviewed local mutant functions",
        "rows": rows,
        "defects": [
            {
                "id": key,
                "description": description,
                "detected_by": [r["method"] for r in rows if key in r["killed"]],
            }
            for key, description in DEFECTS.items()
        ],
        "suites": {
            name: [case.model_dump(mode="json") for case in cases] for name, cases in suites.items()
        },
        "generation_receipts": receipts,
        "policy_sha256": source_hash((ROOT / "data/policies.json").read_text()),
        "benchmark_source_sha256": source_hash(
            (ROOT / "backend/rulereplay/benchmark.py").read_text()
        ),
        "limitations": [
            "Offline boundaries were tuned after observing the D10 leap-day survivor. "
            "This is in-sample defect detection, not a held-out generalization result.",
            "Replay consistency measures saved simulator evidence, not code re-execution or LLM "
            "reproduction. Invalid-test and execution-failure rates cover validated local suites "
            "and reviewed mutant functions only. Costs and tokens are unavailable.",
            "AI ablations have no measurements until explicitly approved live Meta requests run. "
            "Offline boundary results are not evidence of Muse Wonder performance.",
            "Ten deliberately seeded defects in one synthetic policy domain; this is not a "
            "representative financial-software benchmark or proof of general superiority.",
            "All measured methods share the independent oracle as the evaluator. The comparison "
            "isolates input selection, not the quality of manually written expected values.",
            "Each method has a 48-case budget. Evidence gaps are excluded from defect scoring "
            "and reported as unsupported cases. False alarms use the independent correct control.",
            "Random sampling uses one disclosed seed; Hypothesis metamorphic tests are separate. "
            "Wall-clock times vary. No Modal latency or cost has been measured.",
        ],
    }


def report_markdown(result):
    lines = [
        "# RuleReplay benchmark report",
        "",
        "Measured on 2026-10-29. Synthetic data only.",
        "",
        f"Seed: `{SEED}`. Budget: {BUDGET} cases per method. Ten reviewed seeded defects.",
        "",
        "| Method | Cases / supported | Detected | False alarms | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        cases = f"{row['cases']} / {row['supported_cases']}" if row["cases"] is not None else "—"
        detected = f"{row['detected']}/10" if row["detected"] is not None else "—"
        false = str(row["false_alarms"]) if row["false_alarms"] is not None else "—"
        lines.append(f"| {row['method']} | {cases} | {detected} | {false} | {row['status']} |")
    lines += ["", "## Interpretation and limits", ""] + [
        "- " + item for item in result["limitations"]
    ]
    lines += [
        "",
        "## Reproduction",
        "",
        "`uv run python -m rulereplay.benchmark` writes this report "
        "and `benchmarks/results.json`, including every input and first counterexample.",
        "",
        "`--live` makes two billable Meta requests and must only be used after explicit "
        "approval, credentials and the server-side paid gate are enabled. It does not "
        "create Modal resources. AI suites are saved with prompt hashes and model IDs.",
        "",
        "## Defect outcomes",
        "",
    ]
    for defect in result["defects"]:
        lines.append(
            f"- **{defect['id']}** {defect['description']}. Detected by: "
            + (", ".join(defect["detected_by"]) or "none of the measured suites")
            + "."
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Requires explicit approval; two paid calls"
    )
    args = parser.parse_args()
    result = benchmark(live=args.live)
    output = ROOT / "benchmarks"
    output.mkdir(exist_ok=True)
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "REPORT.md").write_text(report_markdown(result))
    for row in result["rows"]:
        print(
            f"{row['method']}: {row['detected'] if row['detected'] is not None else 'not measured'}"
            f" / {row['total_defects']} defects; {row['status']}"
        )


if __name__ == "__main__":
    main()
