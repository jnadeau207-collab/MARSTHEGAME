"""Global settings, constants, and configuration."""

import json
from pathlib import Path

from game.core.accessibility import DEFAULT_ACCESSIBILITY, normalize_runtime_settings
from game.data.content import apply_level_content, build_chapters
from game.data.ip_tracks import get_identity, resolve_ip_track
from game.data.levels import LEVELS

# Paths
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
SAVE_PATH = ROOT / "savegame.json"
SETTINGS_PATH = ROOT / "settings.json"

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
ACTIVE_IP_TRACK = resolve_ip_track()
IDENTITY = get_identity(ACTIVE_IP_TRACK)
TITLE = IDENTITY["game_title"]

# Resolve every runtime chapter display string from stable content keys. The
# original geometry, ids, collision data, and save semantics remain untouched.
CHAPTERS = build_chapters(ACTIVE_IP_TRACK)
apply_level_content(LEVELS, ACTIVE_IP_TRACK)

# Physics / feel — tuned for readable jumps + Starship climb
GRAVITY = 0.58
PLAYER_SPEED = 4.4
PLAYER_JUMP = -14.8
PLAYER_DASH_SPEED = 11.5
PLAYER_DASH_DURATION = 12  # frames
COYOTE_TIME = 10  # frames
JUMP_BUFFER = 10  # frames
HIT_STOP_FRAMES = 4
SHAKE_DECAY = 0.85


# Colors
class Colors:
    BLACK = (8, 8, 12)
    WHITE = (240, 240, 245)
    GRAY = (90, 95, 110)
    DARK = (20, 22, 30)
    ACCENT = (0, 200, 255)
    DANGER = (255, 70, 60)
    SUCCESS = (80, 220, 120)
    GOLD = (255, 200, 60)
    PREORIA_SKY = (180, 140, 90)
    PREORIA_GROUND = (60, 45, 30)
    CANADA_SKY = (140, 180, 220)
    CAMPUS_SKY = (100, 150, 200)
    CORPORATE = (40, 50, 70)
    TESLA_RED = (220, 30, 40)
    SPACEX_BLUE = (20, 40, 80)
    MARS = (180, 80, 50)


DEFAULT_KEYS = {
    "left": ["a", "left"],
    "right": ["d", "right"],
    "up": ["w", "up"],
    "down": ["s", "down"],
    "jump": ["space", "k"],
    "dash": ["lshift", "j"],
    "attack": ["j", "z"],
    "interact": ["e", "f"],
    "pause": ["escape", "p"],
    "confirm": ["return", "space"],
    "cancel": ["escape", "backspace"],
}


def load_settings():
    defaults = {
        "volume_master": 0.7,
        "volume_sfx": 0.8,
        "volume_music": 0.5,
        "volume_ambience": 0.6,
        "volume_dialogue": 0.8,
        "fullscreen": False,
        "show_fps": False,
        "keys": DEFAULT_KEYS.copy(),
        "accessibility": DEFAULT_ACCESSIBILITY.copy(),
    }
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as file:
                data = json.load(file)
                defaults.update(data)
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return normalize_runtime_settings(defaults)


def save_settings(data):
    try:
        normalized = normalize_runtime_settings(data)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
            json.dump(normalized, file, indent=2, sort_keys=True)
    except (OSError, TypeError, ValueError):
        pass
