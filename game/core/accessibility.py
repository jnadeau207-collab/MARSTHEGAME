"""Accessibility settings normalized at the runtime boundary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_ACCESSIBILITY: dict[str, Any] = {
    "reduced_motion": False,
    "screen_shake": 1.0,
    "hit_stop": 1.0,
    "flash_intensity": 1.0,
    "subtitles": True,
    "subtitle_scale": 1.0,
    "high_contrast": False,
    "hold_assist": False,
}


def _clamp(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, numeric))


def normalize_accessibility(value: Any) -> dict[str, Any]:
    """Return a complete, bounded accessibility configuration."""

    source = value if isinstance(value, dict) else {}
    result = deepcopy(DEFAULT_ACCESSIBILITY)
    for key in ("reduced_motion", "subtitles", "high_contrast", "hold_assist"):
        if key in source:
            result[key] = bool(source[key])

    result["screen_shake"] = _clamp(source.get("screen_shake"), 0.0, 1.0, 1.0)
    result["hit_stop"] = _clamp(source.get("hit_stop"), 0.0, 1.0, 1.0)
    result["flash_intensity"] = _clamp(source.get("flash_intensity"), 0.0, 1.0, 1.0)
    result["subtitle_scale"] = _clamp(source.get("subtitle_scale"), 0.75, 2.0, 1.0)

    if result["reduced_motion"]:
        result["screen_shake"] = 0.0
        result["flash_intensity"] = min(result["flash_intensity"], 0.35)
    return result


def normalize_runtime_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Normalize settings in place while preserving unknown future keys."""

    settings["accessibility"] = normalize_accessibility(settings.get("accessibility"))
    for key, fallback in (
        ("volume_master", 0.7),
        ("volume_sfx", 0.8),
        ("volume_music", 0.5),
        ("volume_ambience", 0.6),
        ("volume_dialogue", 0.8),
    ):
        settings[key] = _clamp(settings.get(key), 0.0, 1.0, fallback)
    return settings
