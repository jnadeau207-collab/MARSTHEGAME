"""Procedural event-driven audio with explicit buses and silent fallback."""

from __future__ import annotations

import math
import random
from array import array
from collections import deque
from typing import Any

import pygame

_EVENT_SPECS = {
    "ui_move": (520.0, 0.055, "sine", "ui", 0.38),
    "jump": (360.0, 0.11, "sweep_up", "sfx", 0.55),
    "dash": (150.0, 0.16, "noise", "sfx", 0.72),
    "attack": (230.0, 0.09, "sweep_down", "sfx", 0.62),
    "hurt": (105.0, 0.18, "square", "sfx", 0.75),
    "pickup": (660.0, 0.12, "sweep_up", "sfx", 0.52),
    "terminal": (440.0, 0.24, "pulse", "sfx", 0.62),
    "goal": (330.0, 0.55, "chord", "music", 0.78),
    "death": (90.0, 0.48, "sweep_down", "sfx", 0.8),
}


class AudioDirector:
    """Own audio buses, synthesized cues, adaptive state, and event evidence."""

    def __init__(self, settings: dict[str, Any] | None = None, enabled: bool = True) -> None:
        settings = settings or {}
        self.sample_rate = 22_050
        self.enabled = bool(enabled and pygame.mixer.get_init())
        self.buses = {
            "master": self._clamp(settings.get("volume_master", 0.7)),
            "music": self._clamp(settings.get("volume_music", 0.5)),
            "sfx": self._clamp(settings.get("volume_sfx", 0.8)),
            "ambience": self._clamp(settings.get("volume_ambience", 0.6)),
            "dialogue": self._clamp(settings.get("volume_dialogue", 0.8)),
            "ui": self._clamp(settings.get("volume_sfx", 0.8)),
        }
        self.state = "silence"
        self.intensity = 0.0
        self.event_log: deque[dict[str, Any]] = deque(maxlen=512)
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._last_observed: dict[str, Any] = {}
        self._cooldowns: dict[str, float] = {}
        if self.enabled:
            self._build_sound_bank()

    @staticmethod
    def _clamp(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric))

    def _sample(self, waveform: str, phase: float, progress: float, rng: random.Random) -> float:
        if waveform == "sine":
            return math.sin(phase)
        if waveform == "square":
            return 1.0 if math.sin(phase) >= 0 else -1.0
        if waveform == "noise":
            return rng.uniform(-1.0, 1.0) * (1.0 - progress * 0.5)
        if waveform == "pulse":
            return math.sin(phase) * (1.0 if int(progress * 12) % 2 == 0 else 0.35)
        if waveform == "chord":
            return (
                math.sin(phase) + 0.65 * math.sin(phase * 1.25) + 0.45 * math.sin(phase * 1.5)
            ) / 2.1
        return math.sin(phase)

    def _synthesize(self, frequency: float, duration: float, waveform: str, seed: int) -> bytes:
        frame_count = max(1, int(self.sample_rate * duration))
        samples = array("h")
        rng = random.Random(seed)
        phase = 0.0
        for index in range(frame_count):
            progress = index / frame_count
            if waveform == "sweep_up":
                instantaneous_frequency = frequency * (0.65 + progress * 1.35)
                base_waveform = "sine"
            elif waveform == "sweep_down":
                instantaneous_frequency = frequency * (1.8 - progress * 1.3)
                base_waveform = "sine"
            else:
                instantaneous_frequency = frequency
                base_waveform = waveform
            phase += math.tau * instantaneous_frequency / self.sample_rate
            attack = min(1.0, progress / 0.08)
            release = min(1.0, (1.0 - progress) / 0.22)
            envelope = max(0.0, min(attack, release)) ** 1.35
            value = self._sample(base_waveform, phase, progress, rng) * envelope
            sample = int(max(-1.0, min(1.0, value)) * 17_500)
            samples.append(sample)
            samples.append(sample)
        return samples.tobytes()

    def _build_sound_bank(self) -> None:
        for index, (name, spec) in enumerate(_EVENT_SPECS.items()):
            frequency, duration, waveform, _bus, _volume = spec
            try:
                buffer = self._synthesize(frequency, duration, waveform, index * 7919 + 17)
                self._sounds[name] = pygame.mixer.Sound(buffer=buffer)
            except pygame.error:
                self.enabled = False
                self._sounds.clear()
                break

    def refresh_settings(self, settings: dict[str, Any]) -> None:
        mapping = {
            "master": "volume_master",
            "music": "volume_music",
            "sfx": "volume_sfx",
            "ambience": "volume_ambience",
            "dialogue": "volume_dialogue",
            "ui": "volume_sfx",
        }
        for bus, key in mapping.items():
            self.buses[bus] = self._clamp(settings.get(key, self.buses[bus]))

    def set_bus_volume(self, bus: str, volume: float) -> None:
        if bus not in self.buses:
            raise ValueError(f"Unknown audio bus: {bus}")
        self.buses[bus] = self._clamp(volume)

    def set_state(self, state: str, intensity: float = 0.0) -> None:
        if state not in {"silence", "title", "exploration", "combat", "victory", "failure"}:
            raise ValueError(f"Unknown audio state: {state}")
        self.state = state
        self.intensity = self._clamp(intensity)

    def play(self, event: str, strength: float = 1.0, pan: float = 0.0) -> None:
        if event not in _EVENT_SPECS:
            raise ValueError(f"Unknown audio event: {event}")
        strength = max(0.0, min(2.0, float(strength)))
        pan = max(-1.0, min(1.0, float(pan)))
        _frequency, _duration, _waveform, bus, event_volume = _EVENT_SPECS[event]
        effective = event_volume * strength * self.buses[bus] * self.buses["master"]
        self.event_log.append(
            {
                "event": event,
                "bus": bus,
                "strength": strength,
                "pan": pan,
                "effective_volume": effective,
                "state": self.state,
            }
        )
        if not self.enabled or effective <= 0.0:
            return
        sound = self._sounds.get(event)
        if sound is None:
            return
        channel = sound.play()
        if channel is not None:
            left = effective * (1.0 - max(0.0, pan))
            right = effective * (1.0 + min(0.0, pan))
            channel.set_volume(left, right)

    def observe(self, scene: Any) -> None:
        """Map production scene transitions into audio events and adaptive state."""

        if scene is None:
            self.set_state("silence")
            return

        scene_name = type(scene).__name__
        selected = getattr(scene, "selected", None)
        if selected is not None:
            self.set_state("title", 0.2)
            previous_selected = self._last_observed.get("selected")
            if previous_selected is not None and selected != previous_selected:
                self.play("ui_move", 0.65)
            self._last_observed["selected"] = selected

        player = getattr(scene, "player", None)
        if player is None:
            return

        enemies = getattr(scene, "enemies", ())
        living_enemies = sum(bool(getattr(enemy, "alive", False)) for enemy in enemies)
        self.set_state("combat" if living_enemies else "exploration", min(1.0, living_enemies / 4))

        state = getattr(player, "state", None)
        previous_state = self._last_observed.get("player_state")
        if state != previous_state and state in {"jump", "dash", "attack", "hurt"}:
            self.play(state)
        self._last_observed["player_state"] = state

        hp = getattr(player, "hp", None)
        previous_hp = self._last_observed.get("player_hp")
        if previous_hp is not None and hp is not None and hp < previous_hp:
            self.play("hurt", 1.15)
        self._last_observed["player_hp"] = hp

        alive = bool(getattr(player, "alive", True))
        if self._last_observed.get("player_alive", True) and not alive:
            self.set_state("failure", 1.0)
            self.play("death")
        self._last_observed["player_alive"] = alive

        collectible_total = int(getattr(player, "books", 0)) + int(getattr(player, "parts", 0))
        previous_collectibles = self._last_observed.get("collectibles")
        if previous_collectibles is not None and collectible_total > previous_collectibles:
            self.play("pickup")
        self._last_observed["collectibles"] = collectible_total

        terminals = len(getattr(scene, "terminals_activated", ()))
        previous_terminals = self._last_observed.get("terminals")
        if previous_terminals is not None and terminals > previous_terminals:
            self.play("terminal")
        self._last_observed["terminals"] = terminals

        won = bool(getattr(scene, "won", False))
        if won and not self._last_observed.get("won", False):
            self.set_state("victory", 1.0)
            self.play("goal")
        self._last_observed["won"] = won
        self._last_observed["scene"] = scene_name

    def update(self, dt: float) -> None:
        elapsed = max(0.0, float(dt))
        expired = []
        for event, remaining in self._cooldowns.items():
            remaining -= elapsed
            if remaining <= 0:
                expired.append(event)
            else:
                self._cooldowns[event] = remaining
        for event in expired:
            del self._cooldowns[event]
