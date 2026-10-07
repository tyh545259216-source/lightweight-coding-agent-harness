"""Append-only fsynced JSONL. Ignore only a torn final record, never interior corruption."""

import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SessionCorruptError(ValueError):
    pass


class SessionBusyError(RuntimeError):
    pass


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_bytes().splitlines(keepends=True)
        result: list[dict[str, Any]] = []
        for i, line in enumerate(lines):
            if i == len(lines) - 1 and not line.endswith(b"\n"):
                break
            try:
                record = json.loads(line)
                if (
                    not isinstance(record, dict)
                    or not {"event", "timestamp", "data"} <= record.keys()
                ):
                    raise ValueError("Invalid event envelope")
                if (
                    not isinstance(record["event"], str)
                    or not isinstance(record["timestamp"], str)
                    or not isinstance(record["data"], dict)
                ):
                    raise ValueError("Invalid event envelope types")
                datetime.fromisoformat(record["timestamp"])
            except (ValueError, UnicodeError) as exc:
                raise SessionCorruptError(f"Corrupt session at line {i + 1}") from exc
            result.append(record)
        return result

    def append(self, event: str, data: dict[str, Any]) -> None:
        self.load()  # reject interior corruption before mutating
        if self.path.exists():
            with self.path.open("r+b") as handle:
                raw = handle.read()
                if raw and not raw.endswith(b"\n"):
                    handle.truncate(raw.rfind(b"\n") + 1)
        record = {"event": event, "timestamp": datetime.now(UTC).isoformat(), "data": data}
        encoded = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        with self.path.open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

    @contextmanager
    def lease(self) -> Iterator[None]:
        """OS advisory lock: automatically released on process exit."""
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        with lock_path.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise SessionBusyError("Session is in use by another runner") from exc
            try:
                yield
            finally:
                if sys.platform == "win32":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
