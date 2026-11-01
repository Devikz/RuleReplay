"""Ports at the two I/O seams; pure functions remain ordinary typed functions."""

from typing import Literal, Protocol

from rulereplay.domain import ExecutionResult, TestCase


class ExecutionGateway(Protocol):
    def run(
        self, language: Literal["java", "python"], source: str, case: TestCase
    ) -> ExecutionResult: ...


class EvidenceRepository(Protocol):
    def save(self, payload: dict) -> dict: ...
    def get(self, record_id: str) -> dict: ...
