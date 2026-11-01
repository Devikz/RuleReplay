import json
from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st
from rulereplay.benchmark import BUDGET, benchmark, observed, random_cases
from rulereplay.config import ROOT
from rulereplay.domain import TestCase
from rulereplay.minimize import minimize
from rulereplay.oracle import evaluate
from rulereplay.policies import load_policies
from rulereplay.storage import Store
from rulereplay.verification import VerifyRequest, verify


def test_checked_in_measurements_match_current_benchmark():
    saved = json.loads((ROOT / "benchmarks/results.json").read_text())
    current = benchmark()
    assert current["benchmark_source_sha256"] == saved["benchmark_source_sha256"]
    assert current["policy_sha256"] == saved["policy_sha256"]
    assert current["suites"] == saved["suites"]
    for fresh, previous in zip(current["rows"], saved["rows"], strict=True):
        for key in ("killed", "cases", "supported_cases", "false_alarms"):
            assert fresh[key] == previous[key]


def test_benchmark_records_measured_results_and_pending_ai():
    result = benchmark()
    assert len(result["defects"]) == 10
    for row in result["rows"][:3]:
        assert row["cases"] == BUDGET
        assert row["detected"] == len(row["killed"])
        assert row["false_alarms"] == 0
        assert set(row["counterexamples"]) == set(row["killed"])
    for row in result["rows"][3:]:
        assert row["detected"] is None and row["cases"] is None
    assert random_cases() == random_cases()


def test_all_mutants_have_a_real_counterexample():
    cases = [
        TestCase(
            id=f"case-{offset}-{delay}",
            due_date=date(2026, 10, 25) + timedelta(days=offset),
            payment_date=date(2026, 10, 25) + timedelta(days=offset + delay),
        )
        for offset in range(14)
        for delay in range(-10, 16)
    ]
    cases.append(TestCase(id="leap", due_date="2028-02-28", payment_date="2028-03-07"))
    policies = load_policies()
    for number in range(1, 11):
        assert any(
            observed(case, f"D{number:02d}") != evaluate(case, policies).fee_cents for case in cases
        )


def test_counterexample_minimization(settings, tmp_path):
    request = VerifyRequest(
        cases=[{"id": "shrink", "due_date": "2026-10-30", "payment_date": "2026-11-06"}]
    )
    record = verify(request, settings, load_policies(), Store(tmp_path), Store(tmp_path / "suites"))
    reduced = minimize(record, "shrink")
    assert reduced["case"]["payment_date"] == "2026-11-05"
    assert reduced["expected_cents"] == 2500


@given(st.integers(min_value=0, max_value=200), st.integers(min_value=-10, max_value=30))
def test_translation_within_same_policy(offset, delay):
    due = date(2027, 1, 1)
    original = TestCase(id="base", due_date=due, payment_date=due + timedelta(days=delay))
    translated = TestCase(
        id="shift",
        due_date=due + timedelta(days=offset),
        payment_date=due + timedelta(days=offset + delay),
    )
    assert (
        evaluate(original, load_policies()).fee_cents
        == evaluate(translated, load_policies()).fee_cents
    )
