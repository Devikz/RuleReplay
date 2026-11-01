import json
from pathlib import Path

from rulereplay.config import ROOT
from rulereplay.domain import PolicySet

POLICY_FILE = ROOT / "data" / "policies.json"


def load_policies(path: Path = POLICY_FILE) -> PolicySet:
    return PolicySet.model_validate(json.loads(path.read_text()))
