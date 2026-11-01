import importlib.util

from rulereplay.config import ROOT

spec = importlib.util.spec_from_file_location("security_audit", ROOT / "scripts/security_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_unavailable_feed_is_not_a_clean_audit():
    assert audit.classify("npm", 1, '{"error": "offline"}')["status"] == "UNAVAILABLE"
    assert audit.classify("python", 2, "not JSON")["status"] == "UNAVAILABLE"


def test_findings_are_not_treated_as_feed_failure():
    assert (
        audit.classify(
            "python", 1, '{"dependencies":[{"name":"demo", "vulns":[{"id":"CVE-demo"}]}]}'
        )["status"]
        == "FINDINGS"
    )
    assert (
        audit.classify("npm", 1, '{"vulnerabilities":{"demo":{"severity":"high"}}}')["status"]
        == "FINDINGS"
    )


def test_only_complete_success_is_clean():
    assert audit.classify("python", 0, '{"dependencies":[]}')["status"] == "PASS"
    assert (
        audit.classify("python", 0, '{"dependencies":[{"name":"demo", "skip_reason":"missing"}]}')[
            "status"
        ]
        == "UNAVAILABLE"
    )
