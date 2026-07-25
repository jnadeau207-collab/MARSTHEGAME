"""
Input manager with buffering, coyote support hooks, keyboard + gamepad.
"""

import pygame
from game.core.settings import DEFAULT_KEYS


class InputManager:
    def __init__(self, key_bindings=None):
        self.bindings = key_bindings or DEFAULT_KEYS.copy()
        self.keys_down = set()
        self.keys_pressed = set()   # this frame
        self.keys_released = set()
        self.buffer = {}            # action -> frames remaining
        self.joy = None
        self._init_joystick()

    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joy = pygame.joystick.Joystick(0)
            self.joy.init()

    def rebind(self, action, keys):
        self.bindings[action] = keys if isinstance(keys, list) else [keys]

    def update(self):
        self.keys_pressed.clear()
        self.keys_released.clear()

        # Decay buffers
        for a in list(self.buffer.keys()):
            self.buffer[a] -= 1
            if self.buffer[a] <= 0:
                del self.buffer[a]

        # Keyboard
        pressed = pygame.key.get_pressed()
        key_name_map = {
            pygame.K_a: "a", pygame.K_d: "d", pygame.K_w: "w", pygame.K_s: "s",
            pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
            pygame.K_UP: "up", pygame.K_DOWN: "down",
            pygame.K_SPACE: "space", pygame.K_LSHIFT: "lshift",
            pygame.K_j: "j", pygame.K_k: "k", pygame.K_z: "z",
            pygame.K_e: "e", pygame.K_f: "f",
            pygame.K_ESCAPE: "escape", pygame.K_p: "p",
            pygame.K_RETURN: "return", pygame.K_BACKSPACE: "backspace",
        }

        current = set()
        for k, name in key_name_map.items():
            if pressed[k]:
                current.add(name)

        # Gamepad simple mapping
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
                    current.add("jump")
                    current.add("confirm")
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

        newly = current - self.keys_down
        released = self.keys_down - current
        self.keys_pressed = newly
        self.keys_released = released
        self.keys_down = current

        for action in ("jump", "attack", "dash", "interact"):
            if self.just_pressed(action):
                self.buffer[action] = 10

    def is_held(self, action):
        keys = self.bindings.get(action, [])
        return any(k in self.keys_down for k in keys)

    def just_pressed(self, action):
        keys = self.bindings.get(action, [])
        return any(k in self.keys_pressed for k in keys)

    def just_released(self, action):
        keys = self.bindings.get(action, [])
        return any(k in self.keys_released for k in keys)

    def consume_buffer(self, action):
        if action in self.buffer:
            del self.buffer[action]
            return True
        return False

    def has_buffer(self, action):
        return action in self.buffer

    def get_axis(self):
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
