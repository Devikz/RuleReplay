"""Single-process admission, durable idempotency claims, conservative session budgets."""

import json
import os
import re
from threading import BoundedSemaphore, Lock

from rulereplay.integrity import digest
from rulereplay.lifecycle import RunTrace, event
from rulereplay.storage import RecordError, Store


class OperationError(RuntimeError):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


class Operations:
    def __init__(self, settings):
        self.settings = settings
        self.slots = BoundedSemaphore(settings.max_concurrent_analyses)
        self.lock = Lock()
        self.model_calls = 0
        self.sandbox_calls = 0

    def run(self, kind, payload, key, work, *, model_calls=0, sandbox_calls=0, correlation_id=None):
        if key is not None and not re.fullmatch(r"[a-zA-Z0-9_-]{8,128}", key):
            raise OperationError("Invalid Idempotency-Key.", 422)
        if (model_calls or sandbox_calls) and key is None:
            raise OperationError("Live operations require an Idempotency-Key.", 422)
        if not self.slots.acquire(blocking=False):
            raise OperationError("Analysis capacity is busy; retry later with the same key.", 429)
        trace = RunTrace(correlation_id)
        claim = None
        try:
            # One process is the supported deployment. O_EXCL also prevents two processes
            # from starting the same keyed operation; quotas are deliberately process-local.
            if key:
                directory = self.settings.data_dir / "operations"
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                claim = directory / (digest({"kind": kind, "key": key}) + ".json")
                fingerprint = digest(payload)
                try:
                    fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                except FileExistsError:
                    try:
                        if claim.is_symlink() or claim.stat().st_size > 4096:
                            raise ValueError("Invalid receipt")
                        previous = json.loads(claim.read_text())
                        if previous["fingerprint"] != fingerprint:
                            raise OperationError(
                                "Idempotency key was already used for another request."
                            )
                        if previous["state"] == "COMMITTED":
                            return Store(
                                self.settings.data_dir / kind, self.settings.max_record_bytes
                            ).get(previous["record_id"])
                    except (OSError, ValueError, KeyError, TypeError):
                        raise OperationError(
                            "Invalid operation receipt; manual review required."
                        ) from None
                    raise OperationError(
                        "Operation already accepted or interrupted; review before retry."
                    ) from None
                with os.fdopen(fd, "w") as stream:
                    json.dump(
                        {
                            "fingerprint": fingerprint,
                            "state": "ACCEPTED",
                            "correlation_id": trace.id,
                        },
                        stream,
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
            with self.lock:
                if (
                    self.model_calls + model_calls > self.settings.max_model_calls_per_session
                    or self.sandbox_calls + sandbox_calls > self.settings.max_sandboxes_per_session
                ):
                    raise OperationError(
                        "Session cloud budget exhausted; operator review required.", 429
                    )
                self.model_calls += model_calls
                self.sandbox_calls += sandbox_calls
            result = work(trace)
            if claim:
                temporary = claim.with_suffix(".tmp")
                try:
                    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "w") as stream:
                        json.dump(
                            {
                                "fingerprint": fingerprint,
                                "state": "COMMITTED",
                                "record_id": result["id"],
                                "correlation_id": trace.id,
                            },
                            stream,
                        )
                        stream.flush()
                        os.fsync(stream.fileno())
                    temporary.replace(claim)
                finally:
                    temporary.unlink(missing_ok=True)
            return result
        except BaseException as exc:
            if trace.state not in {"COMPLETED", "NEEDS_REVIEW", "FAILED", "CANCELLED"}:
                trace.transition(
                    "CANCELLED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAILED"
                )
            event("operation_failure", trace.id, category=type(exc).__name__)
            # Failures are persisted without exception text. Accepted claims remain blocked:
            # a failed save cannot prove that no external side effect happened.
            try:
                Store(self.settings.data_dir / "failures", self.settings.max_record_bytes).save(
                    {
                        "correlation_id": trace.id,
                        "state": trace.state,
                        "history": trace.history,
                        "category": type(exc).__name__,
                    }
                )
            except (OSError, RecordError):
                pass
            raise
        finally:
            self.slots.release()
