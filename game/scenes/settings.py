"""User-facing accessibility and presentation settings scene."""

from __future__ import annotations

import math

import pygame

from game.core import gfx
from game.core.accessibility import normalize_runtime_settings
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors, save_settings
from game.scenes.base import Scene

_OPTIONS = (
    ("assist_mode", "Assist Mode", "toggle"),
    ("reduced_motion", "Reduced Motion", "toggle"),
    ("screen_shake", "Camera Shake", "intensity"),
    ("flash_intensity", "Flash Intensity", "intensity"),
    ("high_contrast", "High-Contrast Objectives", "toggle"),
    ("hold_assist", "Hold / Toggle Alternative", "toggle"),
    ("subtitles", "Subtitles", "toggle"),
    ("subtitle_background", "Subtitle Background", "toggle"),
    ("subtitle_scale", "Subtitle Size", "subtitle"),
    ("back", "Return to Title", "action"),
)
_INTENSITY_VALUES = (0.0, 0.35, 0.65, 1.0)
_SUBTITLE_VALUES = (0.75, 1.0, 1.25, 1.5, 2.0)


class SettingsScene(Scene):
    """Expose accessibility settings to keyboard and gamepad users."""

    def __init__(self, engine) -> None:
        super().__init__(engine)
        self.selected = 0
        self.timer = 0.0
        self.message = ""
        self.message_timer = 0.0

    @property
    def accessibility(self) -> dict:
        return self.engine.settings["accessibility"]

    def on_enter(self) -> None:
        self.engine.settings = normalize_runtime_settings(self.engine.settings)
        self.selected = min(self.selected, len(_OPTIONS) - 1)

    def on_exit(self) -> None:
        save_settings(self.engine.settings)

    @staticmethod
    def _cycle(values: tuple[float, ...], current: float, delta: int) -> float:
        index = min(range(len(values)), key=lambda item: abs(values[item] - current))
        return values[(index + delta) % len(values)]

    def _adjust(self, delta: int) -> None:
        key, label, kind = _OPTIONS[self.selected]
        if kind == "action":
            self.engine.go_title()
            return
        if kind == "toggle":
            self.accessibility[key] = not bool(self.accessibility[key])
        elif kind == "intensity":
            self.accessibility[key] = self._cycle(
                _INTENSITY_VALUES,
                float(self.accessibility[key]),
                delta,
            )
        elif kind == "subtitle":
            self.accessibility[key] = self._cycle(
                _SUBTITLE_VALUES,
                float(self.accessibility[key]),
                delta,
            )
        self.engine.settings = normalize_runtime_settings(self.engine.settings)
        self.engine.presentation.refresh_settings(self.engine.settings)
        self.message = f"{label}: {self._value_text(key, kind)}"
        self.message_timer = 120.0
        self.engine.audio.play("ui_move", 0.45)

    def _value_text(self, key: str, kind: str) -> str:
        if kind == "action":
            return ""
        value = self.accessibility[key]
        if kind == "toggle":
            return "ON" if value else "OFF"
        if kind == "subtitle":
            return f"{float(value):.2f}×"
        return f"{round(float(value) * 100):d}%"

    def update(self, dt) -> None:
        self.timer += dt
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
        inp = self.engine.input
        if inp.just_pressed("up"):
            self.selected = (self.selected - 1) % len(_OPTIONS)
        if inp.just_pressed("down"):
            self.selected = (self.selected + 1) % len(_OPTIONS)
        if inp.just_pressed("left"):
            self._adjust(-1)
        if inp.just_pressed("right"):
            self._adjust(1)
        if inp.just_pressed("confirm") or inp.just_pressed("jump"):
            self._adjust(1)
        if inp.just_pressed("cancel") or inp.just_pressed("pause"):
            self.engine.go_title()

    def draw(self, surface) -> None:
        accessibility = self.accessibility
        pulse = 0.0 if accessibility["reduced_motion"] else math.sin(self.timer * 0.04) * 8.0
        gfx.gradient_sky(surface, (5, 8, 20), (18, 10, 28), bands=28)
        gfx.soft_circle(
            surface,
            (20, 55, 95),
            (SCREEN_WIDTH // 2, 120),
            150 + round(pulse),
            layers=5,
        )

        title = self.engine.font_lg.render("ACCESSIBILITY & PRESENTATION", True, Colors.WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 42))
        subtitle = self.engine.font_sm.render(
            "Every mission path must remain readable, controllable, and recoverable.",
            True,
            Colors.ACCENT,
        )
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 92))

        panel = pygame.Surface((780, 500), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 175))
        pygame.draw.rect(panel, (0, 200, 255, 75), panel.get_rect(), 1, border_radius=8)
        surface.blit(panel, (SCREEN_WIDTH // 2 - 390, 130))

        for index, (key, label, kind) in enumerate(_OPTIONS):
            row_y = 150 + index * 44
            selected = index == self.selected
            if selected:
                highlight = pygame.Surface((740, 36), pygame.SRCALPHA)
                highlight.fill((0, 180, 255, 45))
                surface.blit(highlight, (SCREEN_WIDTH // 2 - 370, row_y - 4))
                pygame.draw.rect(
                    surface,
                    Colors.ACCENT,
                    (SCREEN_WIDTH // 2 - 370, row_y - 4, 4, 36),
                )
            label_color = Colors.GOLD if selected else (215, 220, 232)
            label_text = self.engine.font_md.render(label, True, label_color)
            surface.blit(label_text, (SCREEN_WIDTH // 2 - 340, row_y))
            value_text = self._value_text(key, kind)
            if value_text:
                value_color = Colors.WHITE if selected else (155, 175, 195)
                rendered_value = self.engine.font_md.render(value_text, True, value_color)
                surface.blit(
                    rendered_value,
                    (SCREEN_WIDTH // 2 + 330 - rendered_value.get_width(), row_y),
                )

        if self.message_timer > 0 and self.message:
            rendered = self.engine.font_sm.render(self.message, True, Colors.SUCCESS)
            surface.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, 604))

        footer = self.engine.font_sm.render(
            "Arrows / D-pad adjust  ·  Enter / A confirm  ·  Backspace / B return",
            True,
            (130, 145, 165),
        )
        surface.blit(
            footer,
            (SCREEN_WIDTH // 2 - footer.get_width() // 2, SCREEN_HEIGHT - 28),
        )
        gfx.draw_vignette(surface, strength=75)
