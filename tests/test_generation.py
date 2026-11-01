import json

import httpx
import pytest
from rulereplay.config import ConfigurationError, Settings
from rulereplay.fixtures import fixture_sources
from rulereplay.generation import (
    GenerationError,
    GenerationRequest,
    generate_meta,
    normalize_cases,
    offline_cases,
)
from rulereplay.policies import load_policies


def test_offline_is_explicit_and_unique():
    suite = offline_cases(load_policies())
    assert suite.source == "offline_boundary" and suite.model is None
    assert len({case.key for case in suite.cases}) == len(suite.cases) == 16
    assert str(suite.cases[0].due_date) == "2026-10-30"


def test_input_validation_and_deduplication():
    good = {"id": "a", "due_date": "2026-10-30", "payment_date": "2026-11-05"}
    cases, rejected, duplicates = normalize_cases(
        [
            good,
            {**good, "id": "b"},
            {**good, "id": "c", "expected_fee": 0},
            {**good, "id": "d", "payment_date": "not-a-date"},
        ]
    )
    assert (len(cases), rejected, duplicates) == (1, 2, 1)


def test_no_network_without_approval(settings):
    def forbidden(_request):
        pytest.fail("Network must not be called")

    with pytest.raises(ConfigurationError):
        generate_meta(
            settings,
            GenerationRequest(mode="meta"),
            load_policies(),
            fixture_sources(),
            httpx.MockTransport(forbidden),
        )


def enabled():
    return Settings(
        _env_file=None, allow_paid_model_requests=True, model_api_key="synthetic-test-key"
    )


def test_real_protocol_with_mocked_transport():
    def respond(request):
        assert str(request.url) == "https://api.meta.ai/v1/chat/completions"
        data = json.loads(request.content)
        assert data["model"] == "muse-wonder-1.0"
        assert data["response_format"]["type"] == "json_schema"
        assert "approved_policy_evidence" in data["messages"][1]["content"]
        assert "synthetic-test-key" not in request.content.decode()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "analysis": "Check transition",
                                    "cases": [
                                        {
                                            "id": "transition",
                                            "due_date": "2026-10-30",
                                            "payment_date": "2026-11-05",
                                            "rationale": "Payment crosses effective date",
                                        }
                                    ],
                                }
                            )
                        },
                    }
                ]
            },
        )

    suite = generate_meta(
        enabled(),
        GenerationRequest(mode="meta"),
        load_policies(),
        fixture_sources(),
        httpx.MockTransport(respond),
    )
    assert suite.source == "meta_with_policy" and suite.prompt_sha256


@pytest.mark.parametrize(
    "status,body",
    [
        (401, {"error": "synthetic-test-key"}),
        (429, {}),
        (200, {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}),
        (200, {"choices": []}),
    ],
)
def test_provider_errors_are_sanitized(status, body):
    with pytest.raises(GenerationError) as caught:
        generate_meta(
            enabled(),
            GenerationRequest(),
            load_policies(),
            fixture_sources(),
            httpx.MockTransport(lambda _: httpx.Response(status, json=body)),
        )
    assert "synthetic-test-key" not in str(caught.value)


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"choices": None},
        {"choices": [None]},
        {"choices": ["not-an-object"]},
        {"choices": [{"finish_reason": "stop", "message": []}]},
        {"choices": [{"finish_reason": "stop", "message": None}]},
    ],
)
def test_malformed_completion_envelopes_fail_safely(body):
    with pytest.raises(GenerationError):
        generate_meta(
            enabled(),
            GenerationRequest(mode="meta"),
            load_policies(),
            fixture_sources(),
            httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
        )
