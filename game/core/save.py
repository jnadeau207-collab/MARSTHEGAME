"""
Single-slot JSON save: chapter progress + unlocks.
"""

import json
from pathlib import Path
from game.core.settings import SAVE_PATH


class SaveData:
    def __init__(self):
        self.chapter_unlocked = 1
        self.chapter_completed = 0
        self.current_chapter = 1
        self.unlocks = {
            "dash": False,
            "prototype_car": False,
            "starship_board": False,
        }
        self.stats = {
            "deaths": 0,
            "books_collected": 0,
            "code_terminals": 0,
            "rockets_failed": 0,
        }
        self.settings_volume = 0.7

    def to_dict(self):
        return {
            "chapter_unlocked": self.chapter_unlocked,
            "chapter_completed": self.chapter_completed,
            "current_chapter": self.current_chapter,
            "unlocks": self.unlocks,
            "stats": self.stats,
            "settings_volume": self.settings_volume,
        }

    def from_dict(self, d):
        self.chapter_unlocked = d.get("chapter_unlocked", 1)
        self.chapter_completed = d.get("chapter_completed", 0)
        self.current_chapter = d.get("current_chapter", 1)
        self.unlocks = d.get("unlocks", self.unlocks)
        self.stats = d.get("stats", self.stats)
        self.settings_volume = d.get("settings_volume", 0.7)

    def complete_chapter(self, chapter_id):
        self.chapter_completed = max(self.chapter_completed, chapter_id)
        self.chapter_unlocked = max(self.chapter_unlocked, chapter_id + 1)

    def save(self):
        try:
            with open(SAVE_PATH, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load(self):
        if not SAVE_PATH.exists():
            return False
        try:
            with open(SAVE_PATH, "r") as f:
                data = json.load(f)
            self.from_dict(data)
            return True
        except Exception:
            return False

    def reset(self):
        self.__init__()
        if SAVE_PATH.exists():
            SAVE_PATH.unlink(missing_ok=True)
