"""Relay Echo accessibility capabilities derived from normalized settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from game.core.accessibility import normalize_accessibility
from game.data.relay_echo import RELAY_ECHO_CONTRACT

RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS: Final = tuple(
    RELAY_ECHO_CONTRACT["accessibility_requirements"]
)


@dataclass(frozen=True)
class RelayEchoAccessibilityProfile:
    assist_mode: bool
    camera_shake_scale: float
    flash_reduction: float
    hold_toggle_alternatives: bool
    high_contrast_objectives: bool
    reduced_motion: bool
    subtitle_background: bool
    subtitles: bool
    subtitle_scale: float

    @classmethod
    def from_settings(cls, settings: dict[str, Any] | None) -> "RelayEchoAccessibilityProfile":
        source = settings or {}
        accessibility = source.get("accessibility", source)
        normalized = normalize_accessibility(accessibility)
        return cls(
            assist_mode=normalized["assist_mode"],
            camera_shake_scale=normalized["screen_shake"],
            flash_reduction=1.0 - normalized["flash_intensity"],
            hold_toggle_alternatives=normalized["hold_assist"],
            high_contrast_objectives=normalized["high_contrast"],
            reduced_motion=normalized["reduced_motion"],
            subtitle_background=normalized["subtitle_background"],
            subtitles=normalized["subtitles"],
            subtitle_scale=normalized["subtitle_scale"],
        )

    def interaction_radius(self, base: tuple[int, int]) -> tuple[int, int]:
        scale = 1.5 if self.assist_mode else 1.0
        return tuple(max(1, round(value * scale)) for value in base)

    def overload_frames(self, base: int) -> int:
        scale = 1.75 if self.assist_mode else 1.0
        return max(1, round(base * scale))

    def recovery_invulnerability_frames(self) -> int:
        return 180 if self.assist_mode else 90

    def accepts_interact(self, input_manager: Any) -> bool:
        return input_manager.just_pressed("interact") or (
            self.hold_toggle_alternatives and input_manager.is_held("interact")
        )

    def objective_palette(self) -> dict[str, tuple[int, int, int]]:
        if self.high_contrast_objectives:
            return {
                "active": (255, 255, 255),
                "complete": (90, 255, 150),
                "detail": (230, 240, 255),
                "warning": (255, 225, 0),
            }
        return {
            "active": (0, 200, 255),
            "complete": (80, 220, 120),
            "detail": (190, 205, 225),
            "warning": (255, 70, 60),
        }

    def evidence(self) -> dict[str, Any]:
        return {
            "assist_mode": self.assist_mode,
            "camera_shake_scale": self.camera_shake_scale,
            "flash_reduction": self.flash_reduction,
            "hold_toggle_alternatives": self.hold_toggle_alternatives,
            "high_contrast_objectives": self.high_contrast_objectives,
            "reduced_motion": self.reduced_motion,
            "subtitle_background": self.subtitle_background,
            "subtitles": self.subtitles,
            "subtitle_scale": self.subtitle_scale,
        }


def relay_echo_accessibility_profile(
    settings: dict[str, Any] | None,
) -> RelayEchoAccessibilityProfile:
    return RelayEchoAccessibilityProfile.from_settings(settings)


def validate_relay_echo_accessibility_profile(
    profile: RelayEchoAccessibilityProfile,
) -> list[str]:
    errors: list[str] = []
    evidence = profile.evidence()
    missing = sorted(set(RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS).difference(evidence))
    if missing:
        errors.append(f"Relay Echo accessibility evidence is incomplete: {missing}")
    if not 0.0 <= profile.camera_shake_scale <= 1.0:
        errors.append("camera shake scale must be bounded")
    if not 0.0 <= profile.flash_reduction <= 1.0:
        errors.append("flash reduction must be bounded")
    if not 0.75 <= profile.subtitle_scale <= 2.0:
        errors.append("subtitle scale must be bounded")
    if profile.reduced_motion and profile.camera_shake_scale != 0.0:
        errors.append("reduced motion must disable camera shake")
    return sorted(set(errors))
