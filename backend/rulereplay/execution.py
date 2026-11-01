"""No cloud resource is looked up or created until the explicit paid gate passes."""

import json
import logging
from pathlib import Path
from typing import Literal

from modal.exception import TimeoutError as ModalTimeoutError
from pydantic import ValidationError

from rulereplay.config import Settings
from rulereplay.domain import ExecutionResult, TestCase

SANDBOX_LIMITS = {
    "timeout": 30,
    "cpu": (0.25, 1.0),
    "memory": (128, 512),
    "block_network": True,
    "secrets": [],
    "volumes": {},
    "network_file_systems": {},
    "env": {},
    # explicitly disable identity injection
    "include_oidc_identity_token": False,  # nosec B105
}


class ModalExecutor:
    def __init__(self, settings: Settings, sdk=None):
        self.settings = settings
        self.sdk = sdk

    def run(
        self, language: Literal["java", "python"], source: str, case: TestCase
    ) -> ExecutionResult:
        self.settings.require_modal()
        if language not in {"java", "python"} or len(source.encode()) > 50000:
            return ExecutionResult(status="error", error="Invalid language or oversized source.")
        sandbox = None
        try:
            if self.sdk is None:
                import modal

                sdk = modal
            else:
                sdk = self.sdk
            client = sdk.Client.from_credentials(
                self.settings.modal_token_id.get_secret_value(),
                self.settings.modal_token_secret.get_secret_value(),
            )
            app = sdk.App.lookup("rulereplay-execution", create_if_missing=True, client=client)
            image = sdk.Image.debian_slim(python_version="3.12")
            if language == "java":
                image = image.apt_install("openjdk-17-jdk-headless")
            limits = {**SANDBOX_LIMITS, "timeout": self.settings.sandbox_timeout_seconds}
            sandbox = sdk.Sandbox.create(app=app, image=image, client=client, **limits)
            # fixed path in a fresh remote sandbox
            sandbox.filesystem.make_directory("/tmp/work")  # nosec B108
            filename = "LegacyLoan.java" if language == "java" else "loan.py"
            # fixed path in a fresh remote sandbox
            sandbox.filesystem.write_text(source, "/tmp/work/" + filename)  # nosec B108
            runner = Path(__file__).with_name("sandbox_runner.py").read_text()
            # fixed path in a fresh remote sandbox
            sandbox.filesystem.write_text(runner, "/tmp/runner.py")  # nosec B108
            process = sandbox.exec(
                "python",
                "-I",
                # fixed path in a fresh remote sandbox
                "/tmp/runner.py",  # nosec B108
                language,
                str(case.due_date),
                str(case.payment_date),
                timeout=min(20, self.settings.sandbox_timeout_seconds),
                bufsize=-1,
            )
            # The trusted harness emits one bounded JSON line; user stdout stays in capped files.
            output = ""
            for chunk in process.stdout:
                if (
                    len(output.encode()) + len(chunk.encode())
                    > self.settings.max_sandbox_output_bytes
                ):
                    return ExecutionResult(
                        status="error",
                        error=(
                            "Sandbox output exceeded 4 KB."
                            if self.settings.max_sandbox_output_bytes == 4096
                            else "Sandbox output exceeded the configured byte limit."
                        ),
                    )
                output += chunk
            returncode = process.wait()
            # Modal 1.6 maps an exec deadline expiry to -1 in ContainerProcess.wait().
            if returncode == -1:
                return ExecutionResult(status="timeout", error="Sandbox execution timed out.")
            if returncode != 0 or len(output.encode()) > self.settings.max_sandbox_output_bytes:
                return ExecutionResult(status="error", error="Sandbox harness failed.")
            result = ExecutionResult.model_validate(json.loads(output))
            # Treat remote error strings as untrusted, even if the envelope is valid.
            if result.status != "ok":
                result.error = (
                    "Sandbox execution timed out."
                    if result.status == "timeout"
                    else ("Sandbox compilation or execution failed.")
                )
            return result
        except (ValueError, ValidationError):
            return ExecutionResult(status="error", error="Sandbox output failed validation.")
        except (TimeoutError, ModalTimeoutError):
            return ExecutionResult(status="timeout", error="Sandbox execution timed out.")
        except Exception:
            # Provider exceptions may contain credentials or submitted source. Never serialize them.
            return ExecutionResult(
                status="error",
                error="Modal execution failed. Check account access "
                "and connectivity; raw provider details are hidden.",
            )
        finally:
            if sandbox is not None:
                try:
                    sandbox.terminate()
                except Exception:
                    # Lifetime cap remains active even if termination RPC fails.
                    logging.getLogger("rulereplay.events").warning(
                        '{"event":"sandbox_cleanup_failed","lifetime_cap_seconds":30}'
                    )
