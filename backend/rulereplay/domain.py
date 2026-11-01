"""Strict domain contracts shared across API, generation, execution and evidence."""

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def calendar_date(value) -> date:
    """One unambiguous calendar-date contract for inputs, policy and approval evidence."""
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Use YYYY-MM-DD calendar dates")
        value = date.fromisoformat(value)
    if type(value) is not date or not 2000 <= value.year <= 2100:
        raise ValueError("Date must be a calendar date from 2000 through 2100")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class TestCase(StrictModel):
    __test__ = False
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    due_date: date
    payment_date: date
    rationale: str = Field(default="User-supplied case", max_length=500)

    @field_validator("due_date", "payment_date", mode="before")
    @classmethod
    def valid_dates(cls, value):
        return calendar_date(value)

    @property
    def key(self) -> tuple[date, date]:
        return self.due_date, self.payment_date


class Provenance(StrictModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)
    document: str = Field(min_length=1, max_length=200)
    clause: str = Field(min_length=1, max_length=2000)
    approved_by: str = Field(min_length=1, max_length=100)
    approved_on: date
    change_reason: str = Field(min_length=1, max_length=500)

    @field_validator("approved_on", mode="before")
    @classmethod
    def valid_approval_date(cls, value):
        return calendar_date(value)


class Policy(StrictModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", max_length=64)
    version: int = Field(ge=1, le=1000, strict=True)
    name: str = Field(min_length=1, max_length=120)
    status: Literal["approved", "draft"]
    effective_from: date
    effective_until: date | None
    selection_basis: Literal["due_date"] = "due_date"
    grace_days: int = Field(ge=0, le=60, strict=True)
    fee_cents: int = Field(ge=0, le=100000, strict=True)
    currency: Literal["USD"] = "USD"
    supersedes: str | None
    provenance: Provenance

    @field_validator("effective_from", "effective_until", mode="before")
    @classmethod
    def valid_effective_dates(cls, value):
        return None if value is None else calendar_date(value)

    @model_validator(mode="after")
    def valid_range(self):
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("Policy effective_until must follow effective_from")
        if self.status == "approved" and self.provenance.approved_on > self.effective_from:
            raise ValueError("Approval must precede or equal the effective date")
        return self


class PolicySet(StrictModel):
    model_config = ConfigDict(frozen=True)
    policies: tuple[Policy, ...] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def consistent_history(self):
        ids = [p.id for p in self.policies]
        versions = [p.version for p in self.policies]
        if len(set(ids)) != len(ids) or len(set(versions)) != len(versions):
            raise ValueError("Policy IDs and versions must be unique")
        approved = sorted(
            (p for p in self.policies if p.status == "approved"), key=lambda p: p.effective_from
        )
        for earlier, later in zip(approved, approved[1:], strict=False):
            if earlier.effective_until is None or earlier.effective_until > later.effective_from:
                raise ValueError("Approved effective periods must not overlap")
        by_id = {p.id: p for p in self.policies}
        for policy in approved:
            if policy.supersedes:
                previous = by_id.get(policy.supersedes)
                if (
                    previous is None
                    or previous.status != "approved"
                    or previous.version >= policy.version
                    or previous.effective_until != policy.effective_from
                ):
                    raise ValueError("Supersedes must name the contiguous approved predecessor")
        return self


class OracleResult(StrictModel):
    supported: bool = Field(strict=True)
    fee_cents: Annotated[int, Field(ge=0, le=100000, strict=True)] | None
    policy_id: str | None
    days_late: int = Field(ge=0, strict=True)
    grace_days: Annotated[int, Field(ge=0, le=60, strict=True)] | None
    explanation: str
    predecessor_fee_cents: Annotated[int, Field(ge=0, le=100000, strict=True)] | None = None
    predecessor_policy_id: str | None = None

    @model_validator(mode="after")
    def complete_evidence(self):
        fields = (self.fee_cents, self.policy_id, self.grace_days)
        if self.supported and any(value is None for value in fields):
            raise ValueError("Supported oracle result requires policy and financial evidence")
        if not self.supported and any(value is not None for value in fields):
            raise ValueError("Unsupported oracle result cannot establish a fee")
        if (self.predecessor_policy_id is None) != (self.predecessor_fee_cents is None):
            raise ValueError("Predecessor evidence must be complete")
        return self


class ExecutionResult(StrictModel):
    status: Literal["ok", "error", "timeout"]
    fee_cents: Annotated[int, Field(ge=0, le=1000000, strict=True)] | None = None
    error: str | None = Field(default=None, max_length=500)
    duration_ms: float = Field(default=0, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def valid_output(self):
        if self.status == "ok" and self.fee_cents is None:
            raise ValueError("Successful execution requires integer fee_cents")
        if self.status != "ok" and self.fee_cents is not None:
            raise ValueError("Failed execution cannot have a financial result")
        return self


class Verdict(StrEnum):
    COMPLIANT = "compliant"
    REGRESSION = "unauthorized_regression"
    AUTHORIZED = "authorized_policy_change"
    CORRECTED = "corrected_legacy_defect"
    BOTH_WRONG = "both_implementations_wrong"
    INSUFFICIENT = "insufficient_policy_evidence"
    INVALID = "invalid_input"
    EXECUTION_FAILURE = "execution_failure"


class Finding(StrictModel):
    case_id: str
    case: TestCase | None
    oracle: OracleResult | None
    legacy: ExecutionResult | None
    updated: ExecutionResult | None
    verdict: Verdict
    reason: str
