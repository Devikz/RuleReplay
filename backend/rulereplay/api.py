import json
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from pydantic import Field, model_validator

from rulereplay.config import ROOT
from rulereplay.domain import PolicySet
from rulereplay.fixtures import fixture_sources, source_hash
from rulereplay.generation import GenerationRequest, generate_meta, offline_cases
from rulereplay.integrity import digest
from rulereplay.minimize import minimize
from rulereplay.policies import load_policies
from rulereplay.simulator import SCENARIOS, Scenario
from rulereplay.storage import Store
from rulereplay.verification import VerifyRequest, replay, verify

router = APIRouter(prefix="/api")


def stores(request: Request):
    directory = request.app.state.settings.data_dir
    return {
        name: Store(directory / name, max_bytes=request.app.state.settings.max_record_bytes)
        for name in ("runs", "generations", "policy-sets")
    }


def policies_for(request, policy_set_id):
    if policy_set_id:
        return PolicySet.model_validate(
            stores(request)["policy-sets"].get(policy_set_id)["policies"]
        )
    return load_policies()


class GenerateAPIRequest(GenerationRequest):
    scenario: Scenario = "payment_date_bug"
    policy_set_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    java_source: str | None = Field(default=None, min_length=1, max_length=50000)
    python_source: str | None = Field(default=None, min_length=1, max_length=50000)

    @model_validator(mode="after")
    def sources_together(self):
        if (self.java_source is None) != (self.python_source is None):
            raise ValueError("Supply both source files together")
        return self


class VerifyAPIRequest(VerifyRequest):
    policy_set_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


@router.get("/policies")
def policies():
    return load_policies()


@router.get("/policy-sets")
def policy_sets(request: Request):
    return stores(request)["policy-sets"].recent()


@router.post("/policy-sets", status_code=201)
def save_policy_set(payload: PolicySet, request: Request):
    # New immutable snapshot, never overwrites the bundled approved policy evidence.
    return stores(request)["policy-sets"].save(
        {
            "policies": payload.model_dump(mode="json"),
            "created_at": datetime.now(UTC).isoformat(),
        }
    )


@router.get("/fixtures")
def fixtures():
    return [{"id": key, "label": label} for key, label in SCENARIOS.items()]


@router.get("/fixtures/{scenario}")
def fixture(scenario: Scenario):
    sources = fixture_sources(scenario)
    return {"sources": sources, "sha256": {k: source_hash(v) for k, v in sources.items()}}


@router.post("/generate", status_code=201)
def generate(payload: GenerateAPIRequest, request: Request):
    policies = policies_for(request, payload.policy_set_id)
    sources = (
        fixture_sources(payload.scenario)
        if payload.java_source is None
        else {"java": payload.java_source, "python": payload.python_source}
    )
    if payload.mode == "meta":
        request.app.state.settings.require_meta()

    def work(trace):
        trace.transition("VALIDATING")
        trace.transition("GENERATING")
        suite = (
            offline_cases(policies, payload.count)
            if payload.mode == "offline"
            else generate_meta(request.app.state.settings, payload, policies, sources)
        )
        return trace.persist(
            stores(request)["generations"],
            {
                "created_at": datetime.now(UTC).isoformat(),
                "correlation_id": trace.id,
                "metrics": {
                    "model_calls": int(payload.mode == "meta"),
                    "duration_ms": trace.history[-1]["elapsed_ms"],
                },
                "suite": suite.model_dump(mode="json"),
                "source_sha256": {key: source_hash(value) for key, value in sources.items()},
            },
            "NEEDS_REVIEW" if suite.rejected_count else "COMPLETED",
        )

    return request.app.state.operations.run(
        "generations",
        {
            "request": payload.model_dump(mode="json"),
            "policy": digest(policies.model_dump(mode="json")),
            "sources": {key: source_hash(value) for key, value in sources.items()},
        },
        request.headers.get("Idempotency-Key"),
        work,
        model_calls=int(payload.mode == "meta"),
        correlation_id=request.state.correlation_id,
    )


@router.post("/verify", status_code=201)
def run_verification(payload: VerifyAPIRequest, request: Request):
    storage = stores(request)
    policies = policies_for(request, payload.policy_set_id)
    if payload.mode == "modal":
        request.app.state.settings.require_modal()
    sources = (
        fixture_sources(payload.scenario)
        if payload.java_source is None
        else {
            "java": payload.java_source,
            "python": payload.python_source,
        }
    )
    return request.app.state.operations.run(
        "runs",
        {
            "request": payload.model_dump(mode="json"),
            "policy": digest(policies.model_dump(mode="json")),
            "sources": {key: source_hash(value) for key, value in sources.items()},
        },
        request.headers.get("Idempotency-Key"),
        lambda trace: verify(
            payload,
            request.app.state.settings,
            policies,
            storage["runs"],
            storage["generations"],
            trace=trace,
        ),
        correlation_id=request.state.correlation_id,
        # Reserve the upper bound before any potentially billable work. Unused reservations
        # are not refunded: uncertainty must not cause repeated external spending.
        sandbox_calls=(
            request.app.state.settings.max_sandboxes_per_analysis if payload.mode == "modal" else 0
        ),
    )


@router.get("/runs")
def runs(request: Request):
    return [
        {
            **{
                key: record[key]
                for key in ("id", "created_at", "scenario", "summary", "execution_mode")
            },
            # Older records have no authoritative advisory. Never promote the legacy summary.
            "release": record.get("release"),
        }
        for record in stores(request)["runs"].recent()
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: str, request: Request):
    return stores(request)["runs"].get(run_id)


@router.post("/runs/{run_id}/replay")
def replay_run(run_id: str, request: Request):
    return replay(stores(request)["runs"].get(run_id))


@router.get("/benchmarks")
def benchmarks():
    path = ROOT / "benchmarks" / "results.json"
    return json.loads(path.read_text()) if path.exists() else {"status": "not_run"}


@router.post("/runs/{run_id}/minimize/{case_id}")
def minimize_case(run_id: str, case_id: str, request: Request):
    return minimize(stores(request)["runs"].get(run_id), case_id)
