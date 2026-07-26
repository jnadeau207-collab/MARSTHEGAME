"""
Global settings, constants, and configuration.
"""

import json
from pathlib import Path

from game.data.ip_tracks import get_identity

# Paths
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
SAVE_PATH = ROOT / "savegame.json"
SETTINGS_PATH = ROOT / "settings.json"

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
IDENTITY = get_identity()
TITLE = IDENTITY["game_title"]

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

CHAPTERS = [
    {"id": 1, "title": "Pretoria Streets", "subtitle": "Grit & Resolve", "year": "1980s",
     "description": "Young Elon. School bullying. Street survival. Books and parts become weapons of the mind.",
     "palette": "preoria", "playable": True},
    {"id": 2, "title": "Crossing", "subtitle": "Canada & Arrival", "year": "1989–1992",
     "description": "Travel, odd jobs, first terminals. Timing and early code unlock the path forward.",
     "palette": "canada", "playable": True},
    {"id": 3, "title": "College & Zip2", "subtitle": "Ship the Product", "year": "1995",
     "description": "Campus nights and startup pressure. Symbol matching, pipelines, time pressure.",
     "palette": "campus", "playable": True},
    {"id": 4, "title": "X.com / PayPal Wars", "subtitle": "Corporate Arena", "year": "1999–2002",
     "description": "Rival waves and negotiation choices. Resources shift with every decision.",
     "palette": "corporate", "playable": True},
    {"id": 5, "title": "Tesla Factory Floor", "subtitle": "Production Hell", "year": "2008–2010",
     "description": "Automation puzzles, defending the line, prototype unlock.",
     "palette": "tesla", "playable": True},
    {"id": 6, "title": "SpaceX: Failures Before Flight", "subtitle": "Each Boom Teaches", "year": "2006–2010",
     "description": "Assembly, launch windows, recovery. Failure is progress.",
     "palette": "spacex", "playable": True},
    {"id": 7, "title": "Starship to Mars", "subtitle": "Leaving Earth", "year": "Near Future",
     "description": "Docking sequences, G-force rhythm, system triage. Spectacle.",
     "palette": "starship", "playable": True},
    {"id": 8, "title": "Mars Colony", "subtitle": "First City", "year": "Frontier",
     "description": "Land, survive, expand. Oxygen, power, water. Open frontier.",
     "palette": "mars", "playable": True},
]


def load_settings():
    defaults = {
        "volume_master": 0.7,
        "volume_sfx": 0.8,
        "volume_music": 0.5,
        "fullscreen": False,
        "show_fps": False,
        "keys": DEFAULT_KEYS.copy(),
    }
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_settings(data):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
