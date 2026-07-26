"""Checksummed transactional JSON storage with backup recovery."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CheckpointLoadResult:
    payload: dict[str, Any]
    generation: int
    source: str
    repaired_primary: bool = False


class CheckpointError(RuntimeError):
    """Raised when no valid checkpoint candidate can be loaded."""


class TransactionalJsonStore:
    """Persist one JSON payload without exposing partial primary writes."""

    def __init__(self, path: Path, schema_version: int = 1) -> None:
        self.path = Path(path)
        self.backup_path = self.path.with_suffix(self.path.suffix + ".bak")
        self.temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        self.schema_version = int(schema_version)
        if self.schema_version < 1:
            raise ValueError("schema_version must be positive")

    @staticmethod
    def _canonical_bytes(body: dict[str, Any]) -> bytes:
        return json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    def _envelope(self, payload: dict[str, Any], generation: int) -> dict[str, Any]:
        if generation < 1:
            raise ValueError("generation must be positive")
        body = {
            "schema_version": self.schema_version,
            "generation": generation,
            "payload": payload,
        }
        digest = hashlib.sha256(self._canonical_bytes(body)).hexdigest()
        return {**body, "sha256": digest}

    def _decode(self, raw: Any, source: str) -> CheckpointLoadResult:
        if not isinstance(raw, dict):
            raise CheckpointError(f"{source} checkpoint root must be an object")

        if "sha256" not in raw and "payload" not in raw:
            return CheckpointLoadResult(raw, 0, "legacy")

        schema_version = raw.get("schema_version")
        generation = raw.get("generation")
        payload = raw.get("payload")
        digest = raw.get("sha256")
        if schema_version != self.schema_version:
            raise CheckpointError(
                f"{source} checkpoint schema {schema_version!r} does not match {self.schema_version}"
            )
        if not isinstance(generation, int) or generation < 1:
            raise CheckpointError(f"{source} checkpoint generation is invalid")
        if not isinstance(payload, dict):
            raise CheckpointError(f"{source} checkpoint payload must be an object")
        if not isinstance(digest, str):
            raise CheckpointError(f"{source} checkpoint checksum is missing")

        body = {
            "schema_version": schema_version,
            "generation": generation,
            "payload": payload,
        }
        expected = hashlib.sha256(self._canonical_bytes(body)).hexdigest()
        if not hashlib.compare_digest(digest, expected):
            raise CheckpointError(f"{source} checkpoint checksum mismatch")
        return CheckpointLoadResult(payload, generation, source)

    def _read(self, path: Path, source: str) -> CheckpointLoadResult:
        try:
            with path.open("r", encoding="utf-8") as file:
                return self._decode(json.load(file), source)
        except CheckpointError:
            raise
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CheckpointError(f"cannot read {source} checkpoint: {exc}") from exc

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        if not hasattr(os, "O_DIRECTORY"):
            return
        descriptor = None
        try:
            descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            os.fsync(descriptor)
        except OSError:
            pass
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _write_bytes(self, destination: Path, content: bytes) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

    def save(self, payload: dict[str, Any], generation: int) -> None:
        envelope = self._envelope(payload, generation)
        rendered = json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True)
        content = (rendered + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._write_bytes(self.temp_path, content)
            self._read(self.temp_path, "temporary")
            if self.path.exists():
                os.replace(self.path, self.backup_path)
            os.replace(self.temp_path, self.path)
            self._fsync_directory(self.path.parent)
            written = self._read(self.path, "primary")
            if written.generation != generation:
                raise CheckpointError("written checkpoint generation does not match")
        except Exception:
            self.temp_path.unlink(missing_ok=True)
            raise

    def _repair_from_backup(self) -> bool:
        try:
            content = self.backup_path.read_bytes()
            self._write_bytes(self.temp_path, content)
            self._read(self.temp_path, "repair")
            os.replace(self.temp_path, self.path)
            self._fsync_directory(self.path.parent)
            return True
        except Exception:
            self.temp_path.unlink(missing_ok=True)
            return False

    def load(self) -> CheckpointLoadResult:
        primary_error: CheckpointError | None = None
        if self.path.exists():
            try:
                return self._read(self.path, "primary")
            except CheckpointError as exc:
                primary_error = exc

        if self.backup_path.exists():
            try:
                backup = self._read(self.backup_path, "backup")
                repaired = self._repair_from_backup()
                return CheckpointLoadResult(
                    backup.payload,
                    backup.generation,
                    backup.source,
                    repaired_primary=repaired,
                )
            except CheckpointError as backup_error:
                if primary_error is not None:
                    raise CheckpointError(
                        f"primary and backup checkpoints are invalid: {primary_error}; {backup_error}"
                    ) from backup_error
                raise

        if primary_error is not None:
            raise primary_error
        raise FileNotFoundError(self.path)

    def reset(self) -> None:
        for path in (self.path, self.backup_path, self.temp_path):
            path.unlink(missing_ok=True)
