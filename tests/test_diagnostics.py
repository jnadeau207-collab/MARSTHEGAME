from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from game.core.diagnostics import CrashReporter


class CrashReporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name) / "crashes"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_capture_writes_atomic_bounded_report_without_environment_dump(self) -> None:
        reporter = CrashReporter(self.directory)
        reporter.context_provider = lambda: {
            "scene": "TestScene",
            "recent_events": list(range(100)),
            "long_text": "x" * 5000,
        }
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            path = reporter.capture_exception(exc)

        self.assertIsNotNone(path)
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["exception"]["type"], "RuntimeError")
        self.assertEqual(report["exception"]["message"], "boom")
        self.assertIn("RuntimeError: boom", report["exception"]["traceback"])
        self.assertEqual(report["context"]["scene"], "TestScene")
        self.assertEqual(len(report["context"]["recent_events"]), 64)
        self.assertEqual(len(report["context"]["long_text"]), 4096)
        self.assertNotIn("environment", report)
        self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())

    def test_context_provider_failure_does_not_block_report(self) -> None:
        reporter = CrashReporter(self.directory)

        def fail_context():
            raise ValueError("context failed")

        reporter.context_provider = fail_context
        path = reporter.capture_exception(RuntimeError("failure"))
        self.assertIsNotNone(path)
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("context_provider_error", report["context"])

    def test_retention_prunes_old_reports(self) -> None:
        reporter = CrashReporter(self.directory, max_reports=2)
        for index in range(4):
            self.assertIsNotNone(reporter.capture_exception(RuntimeError(f"failure-{index}")))
        self.assertEqual(len(list(self.directory.glob("crash-*.json"))), 2)

    def test_control_flow_exceptions_are_not_reported(self) -> None:
        reporter = CrashReporter(self.directory)
        self.assertIsNone(reporter.capture_exception(SystemExit(0)))
        self.assertIsNone(reporter.capture_exception(KeyboardInterrupt()))
        self.assertFalse(self.directory.exists())

    def test_install_and_uninstall_restore_process_hooks(self) -> None:
        original_system = sys.excepthook
        original_thread = threading.excepthook
        reporter = CrashReporter(self.directory)
        reporter.install(lambda: {"scene": "Installed"})
        try:
            self.assertIsNot(sys.excepthook, original_system)
            self.assertIsNot(threading.excepthook, original_thread)
        finally:
            reporter.uninstall()
        self.assertIs(sys.excepthook, original_system)
        self.assertIs(threading.excepthook, original_thread)


if __name__ == "__main__":
    unittest.main()
