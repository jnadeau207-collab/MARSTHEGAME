"""Input manager with buffering, coyote support hooks, keyboard, and gamepad."""

from __future__ import annotations

from collections.abc import Iterable

import pygame

from game.core.settings import DEFAULT_KEYS

_KEY_NAME_MAP = {
    pygame.K_a: "a",
    pygame.K_d: "d",
    pygame.K_w: "w",
    pygame.K_s: "s",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_SPACE: "space",
    pygame.K_LSHIFT: "lshift",
    pygame.K_j: "j",
    pygame.K_k: "k",
    pygame.K_z: "z",
    pygame.K_e: "e",
    pygame.K_f: "f",
    pygame.K_ESCAPE: "escape",
    pygame.K_p: "p",
    pygame.K_RETURN: "return",
    pygame.K_BACKSPACE: "backspace",
}

_BUFFERED_ACTIONS = ("jump", "attack", "dash", "interact")


class InputManager:
    """Translate hardware or deterministic action frames into gameplay queries."""

    def __init__(self, key_bindings=None, *, initialize_joystick: bool = True):
        self.bindings = key_bindings or DEFAULT_KEYS.copy()
        self.keys_down: set[str] = set()
        self.keys_pressed: set[str] = set()
        self.keys_released: set[str] = set()
        self.buffer: dict[str, int] = {}
        self._pending_pressed: set[str] = set()
        self._pending_released: set[str] = set()
        self.joy = None
        if initialize_joystick:
            self._init_joystick()

    def _init_joystick(self) -> None:
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joy = pygame.joystick.Joystick(0)
            self.joy.init()

    def rebind(self, action, keys) -> None:
        self.bindings[action] = list(keys) if isinstance(keys, list) else [keys]

    def _tick_buffers(self) -> None:
        for action in list(self.buffer):
            self.buffer[action] -= 1
            if self.buffer[action] <= 0:
                del self.buffer[action]

    def _buffer_pressed_actions(self) -> None:
        for action in _BUFFERED_ACTIONS:
            if self.just_pressed(action):
                self.buffer[action] = 10

    def update(self) -> None:
        """Poll and immediately apply one legacy input frame."""

        self.update_from_actions(self._poll_hardware())

    def poll_hardware_frame(self) -> None:
        """Capture hardware edges until the fixed-step simulation consumes them."""

        current = self._poll_hardware()
        self._pending_pressed.update(current - self.keys_down)
        self._pending_released.update(self.keys_down - current)
        self.keys_down = current

    def begin_simulation_step(self) -> None:
        """Expose each pending edge to exactly one simulation step."""

        self.keys_pressed = set(self._pending_pressed)
        self.keys_released = set(self._pending_released)
        self._pending_pressed.clear()
        self._pending_released.clear()
        self._buffer_pressed_actions()

    def end_simulation_step(self) -> None:
        """Advance simulation-time buffers and retire transient edges."""

        self._tick_buffers()
        self.keys_pressed.clear()
        self.keys_released.clear()

    def update_from_actions(self, active_inputs: Iterable[str]) -> None:
        """Apply a deterministic frame of physical keys or virtual actions.

        Virtual action tokens such as ``jump`` and ``dash`` are accepted beside
        physical binding names. This is used by replay tooling and is also the
        representation produced by gamepad buttons.
        """

        self.keys_pressed.clear()
        self.keys_released.clear()
        self._pending_pressed.clear()
        self._pending_released.clear()
        self._tick_buffers()

        current = set(active_inputs)
        self.keys_pressed = current - self.keys_down
        self.keys_released = self.keys_down - current
        self.keys_down = current
        self._buffer_pressed_actions()

    def _poll_hardware(self) -> set[str]:
        pressed = pygame.key.get_pressed()
        current = {name for key, name in _KEY_NAME_MAP.items() if pressed[key]}

        if self.joy:
            try:
                axis_x = self.joy.get_axis(0)
                axis_y = self.joy.get_axis(1)
                if axis_x < -0.4:
                    current.add("left")
                if axis_x > 0.4:
                    current.add("right")
                if axis_y < -0.4:
                    current.add("up")
                if axis_y > 0.4:
                    current.add("down")
                if self.joy.get_button(0):
                    current.update(("jump", "confirm"))
                if self.joy.get_button(1):
                    current.add("attack")
                if self.joy.get_button(2):
                    current.add("dash")
                if self.joy.get_button(3):
                    current.add("interact")
                if self.joy.get_button(7):
                    current.add("pause")
            except Exception:
                pass

        return current

    def _matches_action(self, action: str, state: set[str]) -> bool:
        if action in state:
            return True
        return any(binding in state for binding in self.bindings.get(action, []))

    def is_held(self, action: str) -> bool:
        return self._matches_action(action, self.keys_down)

    def just_pressed(self, action: str) -> bool:
        return self._matches_action(action, self.keys_pressed)

    def just_released(self, action: str) -> bool:
        return self._matches_action(action, self.keys_released)

    def consume_buffer(self, action: str) -> bool:
        if action in self.buffer:
            del self.buffer[action]
            return True
        return False

    def has_buffer(self, action: str) -> bool:
        return action in self.buffer

    def get_axis(self) -> tuple[int, int]:
        x = 0
        if self.is_held("left"):
            x -= 1
        if self.is_held("right"):
            x += 1
        y = 0
        if self.is_held("up"):
            y -= 1
        if self.is_held("down"):
            y += 1
        return x, y
