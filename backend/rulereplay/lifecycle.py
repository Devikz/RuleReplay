"""Synchronous run lifecycle and safe structured events; no uploaded content is logged."""

import json
import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from rulereplay.contracts import EvidenceRepository

LOGGER = logging.getLogger("rulereplay.events")
TRANSITIONS = {
    "CREATED": {"VALIDATING", "FAILED", "CANCELLED"},
    "VALIDATING": {"GENERATING", "EXECUTING", "FAILED", "CANCELLED"},
    "GENERATING": {"EXECUTING", "COMPLETED", "NEEDS_REVIEW", "FAILED", "CANCELLED"},
    "EXECUTING": {"EVALUATING", "FAILED", "CANCELLED"},
    "EVALUATING": {"COMPLETED", "NEEDS_REVIEW", "FAILED", "CANCELLED"},
    "COMPLETED": set(),
    "NEEDS_REVIEW": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}


def configure_logging():
    """Enable JSON events under Uvicorn, which configures only its own loggers."""
    LOGGER.setLevel(logging.INFO)
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)


def event(name: str, correlation_id: str, **safe_fields):
    LOGGER.info(json.dumps({"event": name, "correlation_id": correlation_id, **safe_fields}))


class RunTrace:
    def __init__(self, correlation_id=None):
        self.id = correlation_id or uuid4().hex
        self.started = time.perf_counter()
        self.state = "CREATED"
        self.history = []
        self._record()

    def _record(self):
        item = {
            "state": self.state,
            "at": datetime.now(UTC).isoformat(),
            "elapsed_ms": round((time.perf_counter() - self.started) * 1000, 3),
        }
        self.history.append(item)
        event("stage_transition", self.id, **item)

    def transition(self, target: str):
        if target not in TRANSITIONS.get(self.state, set()):
            raise ValueError("Illegal analysis lifecycle transition")
        self.state = target
        self._record()

    def persist(self, store: EvidenceRepository, payload: dict, terminal: str):
        """Only publish a terminal state when the atomic evidence write succeeds."""
        if terminal not in TRANSITIONS.get(self.state, set()):
            raise ValueError("Illegal analysis lifecycle transition")
        item = {
            "state": terminal,
            "at": datetime.now(UTC).isoformat(),
            "elapsed_ms": round((time.perf_counter() - self.started) * 1000, 3),
        }
        history = [*self.history, item]
        metrics = {
            **payload.get("metrics", {}),
            "duration_ms": item["elapsed_ms"],
            "stage_duration_ms": {
                before["state"]: round(after["elapsed_ms"] - before["elapsed_ms"], 3)
                for before, after in zip(history, history[1:], strict=False)
            },
        }
        storing = time.perf_counter()
        result = store.save(
            {
                **payload,
                "correlation_id": self.id,
                "metrics": metrics,
                "lifecycle": {"state": terminal, "history": [*self.history, item]},
            }
        )
        event(
            "evidence_persisted",
            self.id,
            duration_ms=round((time.perf_counter() - storing) * 1000, 3),
        )
        self.state = terminal
        self.history.append(item)
        event("stage_transition", self.id, **item)
        return result
