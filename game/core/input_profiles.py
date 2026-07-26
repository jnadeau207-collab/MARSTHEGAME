"""Stable deterministic input profiles used to prove device parity."""

from __future__ import annotations

from typing import Final

from game.core.settings import DEFAULT_KEYS

INPUT_PROFILE_KEYBOARD: Final = "keyboard"
INPUT_PROFILE_GAMEPAD: Final = "gamepad"
INPUT_PROFILES: Final = (INPUT_PROFILE_KEYBOARD, INPUT_PROFILE_GAMEPAD)

REQUIRED_GAMEPLAY_ACTIONS: Final = (
    "left",
    "right",
    "up",
    "down",
    "jump",
    "dash",
    "attack",
    "interact",
    "pause",
    "confirm",
    "cancel",
)

_KEYBOARD_TOKENS: Final = {
    "left": "a",
    "right": "d",
    "up": "w",
    "down": "s",
    "jump": "space",
    "dash": "lshift",
    "attack": "j",
    "interact": "e",
    "pause": "p",
    "confirm": "return",
    "cancel": "backspace",
}
_GAMEPAD_TOKENS: Final = {action: action for action in REQUIRED_GAMEPLAY_ACTIONS}


def input_token(profile: str, action: str) -> str:
    """Return the physical or virtual token used by a deterministic profile."""

    if action not in REQUIRED_GAMEPLAY_ACTIONS:
        raise ValueError(f"unknown gameplay action: {action}")
    if profile == INPUT_PROFILE_KEYBOARD:
        return _KEYBOARD_TOKENS[action]
    if profile == INPUT_PROFILE_GAMEPAD:
        return _GAMEPAD_TOKENS[action]
    raise ValueError(f"unknown input profile: {profile}")


def input_frame(profile: str, *actions: str) -> set[str]:
    """Build one deterministic input frame for a profile."""

    return {input_token(profile, action) for action in actions}


def validate_input_profiles() -> list[str]:
    """Return stable errors when either parity profile loses semantic coverage."""

    errors: list[str] = []
    for action in REQUIRED_GAMEPLAY_ACTIONS:
        keyboard = _KEYBOARD_TOKENS.get(action)
        gamepad = _GAMEPAD_TOKENS.get(action)
        if keyboard not in DEFAULT_KEYS.get(action, ()):
            errors.append(f"keyboard profile does not bind {action}")
        if gamepad != action:
            errors.append(f"gamepad profile does not expose semantic action {action}")
    if set(_KEYBOARD_TOKENS) != set(REQUIRED_GAMEPLAY_ACTIONS):
        errors.append("keyboard profile action coverage is incomplete")
    if set(_GAMEPAD_TOKENS) != set(REQUIRED_GAMEPLAY_ACTIONS):
        errors.append("gamepad profile action coverage is incomplete")
    return sorted(set(errors))
