#!/usr/bin/env python3
"""Compare same-runner Classic Mode performance reports against a robust policy."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

_METRICS = (
    "setup_ms",
    "update_ms_per_frame",
    "draw_ms_per_frame",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load JSON report {path}: {exc}") from exc


def _chapter_map(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(chapter["chapter_id"]): chapter for chapter in report["chapters"]}


def _metric_samples(chapter: dict[str, Any], metric: str) -> list[float]:
    try:
        raw = chapter["metrics"][metric]["samples"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Report is missing samples for {metric}") from exc
    values = [float(value) for value in raw]
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError(f"Report contains invalid samples for {metric}")
    return values


def _validate_report(report: dict[str, Any], label: str, minimum_rounds: int) -> None:
    if report.get("schema_version") != 2:
        raise ValueError(f"{label} must use performance schema version 2")
    if report.get("status") != "pass":
        raise ValueError(f"{label} is not a successful benchmark report")
    if len(report.get("chapters", [])) != 8:
        raise ValueError(f"{label} must contain all eight Classic Mode chapters")
    chapter_ids = sorted(_chapter_map(report))
    if chapter_ids != list(range(1, 9)):
        raise ValueError(f"{label} chapter ids changed: {chapter_ids}")

    rounds = report.get("parameters", {}).get("rounds")
    if not isinstance(rounds, int) or rounds < minimum_rounds:
        raise ValueError(f"{label} must contain at least {minimum_rounds} measured rounds")

    for chapter in report["chapters"]:
        for metric in _METRICS:
            samples = _metric_samples(chapter, metric)
            if len(samples) < minimum_rounds:
                raise ValueError(
                    f"{label} chapter {chapter['chapter_id']} {metric} has too few samples"
                )


def _compatible_parameters(report: dict[str, Any]) -> dict[str, Any]:
    parameters = report.get("parameters", {})
    return {
        "update_frames": parameters.get("update_frames"),
        "draw_frames": parameters.get("draw_frames"),
        "resolution": parameters.get("resolution"),
    }


def _median_absolute_deviation(values: list[float], center: float) -> float:
    return statistics.median(abs(value - center) for value in values)


def evaluate_reports(
    baseline_reports: list[dict[str, Any]],
    candidate_report: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a candidate against one or more same-runner baseline reports."""

    if not baseline_reports:
        raise ValueError("At least one baseline report is required")
    if policy.get("schema_version") != 1:
        raise ValueError("Performance policy must use schema version 1")

    minimum_rounds = int(policy.get("minimum_rounds", 5))
    for index, report in enumerate(baseline_reports, start=1):
        _validate_report(report, f"baseline[{index}]", minimum_rounds)
    _validate_report(candidate_report, "candidate", minimum_rounds)

    expected_parameters = _compatible_parameters(candidate_report)
    for index, report in enumerate(baseline_reports, start=1):
        if _compatible_parameters(report) != expected_parameters:
            raise ValueError(f"baseline[{index}] parameters do not match candidate parameters")

    baseline_python = ".".join(str(baseline_reports[0]["python"]).split(".")[:2])
    candidate_python = ".".join(str(candidate_report["python"]).split(".")[:2])
    if baseline_python != candidate_python:
        raise ValueError("Baseline and candidate Python major/minor versions differ")

    baseline_chapters = [_chapter_map(report) for report in baseline_reports]
    candidate_chapters = _chapter_map(candidate_report)
    metric_results: dict[str, Any] = {}
    failures: list[str] = []

    for metric in _METRICS:
        metric_policy = policy["metrics"][metric]
        relative_floor = float(metric_policy["relative_floor"])
        absolute_floor = float(metric_policy["absolute_floor_ms"])
        mad_multiplier = float(metric_policy["mad_multiplier"])
        aggregate_relative_limit = float(metric_policy["aggregate_relative_limit"])

        chapter_results = []
        baseline_total = 0.0
        candidate_total = 0.0

        for chapter_id in range(1, 9):
            baseline_samples = [
                sample
                for chapters in baseline_chapters
                for sample in _metric_samples(chapters[chapter_id], metric)
            ]
            candidate_samples = _metric_samples(candidate_chapters[chapter_id], metric)

            baseline_center = statistics.median(baseline_samples)
            baseline_mad = _median_absolute_deviation(baseline_samples, baseline_center)
            candidate_center = statistics.median(candidate_samples)
            allowed_delta = max(
                absolute_floor,
                baseline_center * relative_floor,
                baseline_mad * mad_multiplier,
            )
            limit = baseline_center + allowed_delta
            passed = candidate_center <= limit
            ratio = candidate_center / baseline_center if baseline_center else 1.0

            if not passed:
                failures.append(
                    f"{metric} chapter {chapter_id}: {candidate_center:.6f} ms > {limit:.6f} ms"
                )

            baseline_total += baseline_center
            candidate_total += candidate_center
            chapter_results.append(
                {
                    "chapter_id": chapter_id,
                    "baseline_median": baseline_center,
                    "baseline_mad": baseline_mad,
                    "candidate_median": candidate_center,
                    "allowed_delta": allowed_delta,
                    "limit": limit,
                    "ratio": ratio,
                    "status": "pass" if passed else "fail",
                }
            )

        aggregate_ratio = candidate_total / baseline_total if baseline_total else 1.0
        aggregate_passed = aggregate_ratio <= 1.0 + aggregate_relative_limit
        if not aggregate_passed:
            failures.append(
                f"{metric} aggregate ratio {aggregate_ratio:.4f} exceeds "
                f"{1.0 + aggregate_relative_limit:.4f}"
            )

        metric_results[metric] = {
            "aggregate_ratio": aggregate_ratio,
            "aggregate_limit": 1.0 + aggregate_relative_limit,
            "aggregate_status": "pass" if aggregate_passed else "fail",
            "chapters": chapter_results,
        }

    return {
        "schema_version": 1,
        "policy": policy.get("policy_name", "unnamed"),
        "status": "pass" if not failures else "fail",
        "baseline_reports": len(baseline_reports),
        "candidate_git_sha": candidate_report.get("git_sha"),
        "parameters": expected_parameters,
        "metrics": metric_results,
        "failures": failures,
    }


def _write_report(report: dict[str, Any], path: Path | None) -> None:
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = evaluate_reports(
            [_load_json(path) for path in args.baseline],
            _load_json(args.candidate),
            _load_json(args.policy),
        )
    except Exception as exc:
        report = {
            "schema_version": 1,
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_report(report, args.json_out)
        return 2

    _write_report(report, args.json_out)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
