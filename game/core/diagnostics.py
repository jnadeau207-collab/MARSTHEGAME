"""Structured crash diagnostics with bounded context and atomic writes."""

from __future__ import annotations

import json
import os
import platform
import sys
import threading
import traceback
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from game.core.settings import ROOT


class CrashReporter:
    """Capture uncaught failures without collecting environment variables or secrets."""

    def __init__(self, directory: Path | None = None, max_reports: int = 20) -> None:
        if max_reports < 1:
            raise ValueError("max_reports must be positive")
        self.directory = Path(directory) if directory is not None else ROOT / "crashes"
        self.max_reports = max_reports
        self.context_provider: Callable[[], dict[str, Any]] | None = None
        self.last_error: str | None = None
        self._installed = False
        self._original_sys_hook = sys.excepthook
        self._original_thread_hook = getattr(threading, "excepthook", None)

    @classmethod
    def _sanitize(cls, value: Any, depth: int = 0) -> Any:
        if depth >= 6:
            return "<depth-limit>"
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return value[:4096]
        if isinstance(value, dict):
            items = list(value.items())[:64]
            return {str(key)[:128]: cls._sanitize(item, depth + 1) for key, item in items}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [cls._sanitize(item, depth + 1) for item in list(value)[:64]]
        return repr(value)[:1024]

    def _context(self) -> dict[str, Any]:
        if self.context_provider is None:
            return {}
        try:
            provided = self.context_provider()
        except Exception as exc:
            return {"context_provider_error": f"{type(exc).__name__}: {exc}"}
        if not isinstance(provided, dict):
            return {"context_provider_error": "context provider did not return an object"}
        return self._sanitize(provided)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        try:
            with temp.open("w", encoding="utf-8", newline="\n") as file:
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def _prune(self) -> None:
        reports = sorted(
            self.directory.glob("crash-*.json"),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        for stale in reports[self.max_reports :]:
            stale.unlink(missing_ok=True)

    def capture_exception(
        self,
        exc: BaseException,
        *,
        traceback_object=None,
        extra_context: dict[str, Any] | None = None,
    ) -> Path | None:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            return None
        occurred_at = datetime.now(UTC)
        report_id = uuid.uuid4().hex
        path = self.directory / f"crash-{occurred_at:%Y%m%dT%H%M%S.%fZ}-{report_id}.json"
        active_traceback = traceback_object if traceback_object is not None else exc.__traceback__
        context = self._context()
        if extra_context:
            context.update(self._sanitize(extra_context))
        report = {
            "schema_version": 1,
            "report_id": report_id,
            "occurred_at": occurred_at.isoformat(),
            "exception": {
                "type": type(exc).__name__,
                "message": str(exc)[:4096],
                "traceback": "".join(
                    traceback.format_exception(type(exc), exc, active_traceback)
                )[-32_768:],
            },
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "process_id": os.getpid(),
            },
            "context": context,
        }
        try:
            rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            self._atomic_write(path, rendered)
            self._prune()
            self.last_error = None
            return path
        except Exception as write_error:
            self.last_error = f"{type(write_error).__name__}: {write_error}"
            return None

    def install(self, context_provider: Callable[[], dict[str, Any]] | None = None) -> None:
        self.context_provider = context_provider
        if self._installed:
            return
        self._installed = True

        def system_hook(exc_type, exc, traceback_object) -> None:
            self.capture_exception(exc, traceback_object=traceback_object)
            self._original_sys_hook(exc_type, exc, traceback_object)

        def thread_hook(args) -> None:
            self.capture_exception(
                args.exc_value,
                traceback_object=args.exc_traceback,
                extra_context={"thread": getattr(args.thread, "name", None)},
            )
            if self._original_thread_hook is not None:
                self._original_thread_hook(args)

        sys.excepthook = system_hook
        if hasattr(threading, "excepthook"):
            threading.excepthook = thread_hook

    def uninstall(self) -> None:
        if not self._installed:
            return
        sys.excepthook = self._original_sys_hook
        if self._original_thread_hook is not None and hasattr(threading, "excepthook"):
            threading.excepthook = self._original_thread_hook
        self._installed = False
