"""Atomic, immutable, content-checked local records. Hashes are not digital signatures."""

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from rulereplay.evidence import validate_context
from rulereplay.integrity import digest


class RecordError(RuntimeError):
    pass


class Store:
    def __init__(self, directory: Path, max_bytes: int = 2_000_000):
        self.directory = directory
        self.max_bytes = max_bytes

    def save(self, payload: dict) -> dict:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        record_id = uuid4().hex
        record = {**payload, "id": record_id}
        record["integrity_sha256"] = digest(record)
        data = json.dumps(record, indent=2).encode()
        if len(data) > self.max_bytes:
            raise RecordError("Evidence record exceeds the size limit.")
        temp = self.directory / ("." + record_id + ".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            temp.replace(self.directory / (record_id + ".json"))
        finally:
            temp.unlink(missing_ok=True)
        return record

    def get(self, record_id: str) -> dict:
        if not isinstance(record_id, str) or not re.fullmatch(r"[a-f0-9]{32}", record_id):
            raise RecordError("Invalid record identifier.")
        path = self.directory / (record_id + ".json")
        try:
            if path.is_symlink() or path.stat().st_size > self.max_bytes:
                raise RecordError("Invalid evidence file.")
            record = json.loads(path.read_text())
            if not isinstance(record, dict):
                raise RecordError("Evidence record is missing or invalid.")
            checksum = record.pop("integrity_sha256", None)
            if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
                raise RecordError("Evidence record is missing or invalid.")
            if digest(record) != checksum or record.get("id") != record_id:
                raise RecordError("Evidence integrity verification failed.")
            if "oracle_version" in record:
                validate_context(record)
            return {**record, "integrity_sha256": checksum}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise RecordError("Evidence record is missing or invalid.") from None

    def recent(self, limit: int = 20) -> list[dict]:
        paths = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [self.get(path.stem) for path in paths[:limit]]
