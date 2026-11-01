"""Root dotenv loading with secret-safe errors and explicit paid-operation gates."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_API = "https://api.meta.ai/v1"
OFFICIAL_MODEL = "muse-wonder-1.0"


class ConfigurationError(RuntimeError):
    """Only safe, fixed messages and setting names may appear in this error."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        hide_input_in_errors=True,
    )
    model_api_key: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    model_api_base_url: str = OFFICIAL_API
    meta_model: str = OFFICIAL_MODEL
    modal_token_id: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    modal_token_secret: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    allow_paid_model_requests: bool = False
    allow_billable_modal: bool = False
    max_concurrent_analyses: int = Field(default=1, ge=1, le=4)
    max_model_calls_per_session: int = Field(default=4, ge=0, le=20)
    max_sandboxes_per_session: int = Field(default=64, ge=0, le=128)
    max_tests_per_analysis: int = Field(default=48, ge=1, le=48)
    max_sandboxes_per_analysis: int = Field(default=32, ge=2, le=32)
    max_request_bytes: int = Field(default=256000, ge=1024, le=256000)
    max_model_response_bytes: int = Field(default=256000, ge=1024, le=256000)
    max_sandbox_output_bytes: int = Field(default=4096, ge=256, le=4096)
    sandbox_timeout_seconds: int = Field(default=30, ge=5, le=30)
    max_record_bytes: int = Field(default=2_000_000, ge=10000, le=2_000_000)
    data_dir: Path = ROOT / ".local" / "reports"

    @field_validator("model_api_base_url")
    @classmethod
    def official_endpoint(cls, value: str) -> str:
        if value.rstrip("/") != OFFICIAL_API:
            raise ValueError("MODEL_API_BASE_URL must be the official Meta HTTPS endpoint")
        return OFFICIAL_API

    @field_validator("meta_model")
    @classmethod
    def official_model(cls, value: str) -> str:
        if value != OFFICIAL_MODEL:
            raise ValueError("META_MODEL must be the documented Muse Wonder model identifier")
        return value

    @staticmethod
    def has_secret(value: SecretStr) -> bool:
        raw = value.get_secret_value().strip()
        return (
            bool(raw)
            and raw.lower()
            not in {
                "placeholder",
                "changeme",
                "your-api-key",
                "your-api-key-here",
                "replace-me",
            }
            and not raw.startswith("<")
        )

    def require_meta(self) -> None:
        if not self.allow_paid_model_requests:
            raise ConfigurationError(
                "Paid Meta requests are disabled. Explicit approval is required before "
                "enabling ALLOW_PAID_MODEL_REQUESTS. Use offline generation meanwhile."
            )
        if not self.has_secret(self.model_api_key):
            raise ConfigurationError("Set MODEL_API_KEY privately in the root .env file.")

    def require_modal(self) -> None:
        if not self.allow_billable_modal:
            raise ConfigurationError(
                "Billable Modal execution is disabled. Explicit approval is required before "
                "enabling ALLOW_BILLABLE_MODAL. Use the trusted fixture simulator meanwhile."
            )
        missing = [
            name
            for name in ("modal_token_id", "modal_token_secret")
            if not self.has_secret(getattr(self, name))
        ]
        if missing:
            raise ConfigurationError(
                "Set " + ", ".join(n.upper() for n in missing) + " privately in the root .env file."
            )

    def public_status(self) -> dict:
        return {
            "model": self.meta_model,
            "meta": {
                "enabled": self.allow_paid_model_requests,
                "configured": self.has_secret(self.model_api_key),
            },
            "modal": {
                "enabled": self.allow_billable_modal,
                "configured": self.has_secret(self.modal_token_id)
                and self.has_secret(self.modal_token_secret),
            },
        }


def load_settings(**kwargs) -> Settings:
    try:
        settings = Settings(**kwargs)
    except ValidationError as exc:
        fields = sorted({str(e["loc"][0]).upper() for e in exc.errors() if e["loc"]})
        raise ConfigurationError(
            "Invalid configuration: "
            + ", ".join(fields)
            + ". Check .env.example; values are hidden."
        ) from None
    if settings.allow_paid_model_requests:
        settings.require_meta()
    if settings.allow_billable_modal:
        settings.require_modal()
    return settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()
