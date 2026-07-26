"""Validated, transactional single-slot progression save."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from game.core.checkpoint import CheckpointError, CheckpointLoadResult, TransactionalJsonStore
from game.core.settings import SAVE_PATH

_DEFAULT_UNLOCKS = {
    "dash": False,
    "prototype_car": False,
    "starship_board": False,
}
_DEFAULT_STATS = {
    "deaths": 0,
    "books_collected": 0,
    "code_terminals": 0,
    "rockets_failed": 0,
}


class SaveData:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else Path(SAVE_PATH)
        self.store = TransactionalJsonStore(self.path, schema_version=1)
        self.generation = 0
        self.last_load_source: str | None = None
        self.repaired_primary = False
        self.last_error: str | None = None
        self._reset_values()

    def _reset_values(self) -> None:
        self.chapter_unlocked = 1
        self.chapter_completed = 0
        self.current_chapter = 1
        self.unlocks = dict(_DEFAULT_UNLOCKS)
        self.stats = dict(_DEFAULT_STATS)
        self.settings_volume = 0.7

    @staticmethod
    def _bounded_int(value: Any, minimum: int, maximum: int, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field} must be an integer")
        if value < minimum or value > maximum:
            raise ValueError(f"{field} must be between {minimum} and {maximum}")
        return value

    @staticmethod
    def _bounded_float(value: Any, minimum: float, maximum: float, field: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        numeric = float(value)
        if numeric < minimum or numeric > maximum:
            raise ValueError(f"{field} must be between {minimum} and {maximum}")
        return numeric

    @staticmethod
    def _validated_flags(value: Any) -> dict[str, bool]:
        if value is None:
            return dict(_DEFAULT_UNLOCKS)
        if not isinstance(value, dict):
            raise ValueError("unlocks must be an object")
        result = dict(_DEFAULT_UNLOCKS)
        for key in result:
            if key in value:
                if not isinstance(value[key], bool):
                    raise ValueError(f"unlock {key} must be boolean")
                result[key] = value[key]
        return result

    @staticmethod
    def _validated_stats(value: Any) -> dict[str, int]:
        if value is None:
            return dict(_DEFAULT_STATS)
        if not isinstance(value, dict):
            raise ValueError("stats must be an object")
        result = dict(_DEFAULT_STATS)
        for key in result:
            if key in value:
                stat = value[key]
                if isinstance(stat, bool) or not isinstance(stat, int) or stat < 0:
                    raise ValueError(f"stat {key} must be a non-negative integer")
                result[key] = stat
        return result

    def _validated_state(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("save payload must be an object")
        chapter_unlocked = self._bounded_int(
            data.get("chapter_unlocked", 1),
            1,
            9,
            "chapter_unlocked",
        )
        chapter_completed = self._bounded_int(
            data.get("chapter_completed", 0),
            0,
            8,
            "chapter_completed",
        )
        current_chapter = self._bounded_int(
            data.get("current_chapter", 1),
            1,
            8,
            "current_chapter",
        )
        if chapter_completed > chapter_unlocked:
            raise ValueError("chapter_completed cannot exceed chapter_unlocked")
        if current_chapter > chapter_unlocked:
            raise ValueError("current_chapter cannot exceed chapter_unlocked")
        return {
            "chapter_unlocked": chapter_unlocked,
            "chapter_completed": chapter_completed,
            "current_chapter": current_chapter,
            "unlocks": self._validated_flags(data.get("unlocks")),
            "stats": self._validated_stats(data.get("stats")),
            "settings_volume": self._bounded_float(
                data.get("settings_volume", 0.7),
                0.0,
                1.0,
                "settings_volume",
            ),
        }

    def _apply_state(self, state: dict[str, Any]) -> None:
        self.chapter_unlocked = state["chapter_unlocked"]
        self.chapter_completed = state["chapter_completed"]
        self.current_chapter = state["current_chapter"]
        self.unlocks = dict(state["unlocks"])
        self.stats = dict(state["stats"])
        self.settings_volume = state["settings_volume"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter_unlocked": self.chapter_unlocked,
            "chapter_completed": self.chapter_completed,
            "current_chapter": self.current_chapter,
            "unlocks": dict(self.unlocks),
            "stats": dict(self.stats),
            "settings_volume": self.settings_volume,
        }

    def from_dict(self, data: Any) -> None:
        self._apply_state(self._validated_state(data))

    def complete_chapter(self, chapter_id: int) -> None:
        chapter_id = self._bounded_int(chapter_id, 1, 8, "chapter_id")
        self.chapter_completed = max(self.chapter_completed, chapter_id)
        self.chapter_unlocked = max(self.chapter_unlocked, chapter_id + 1)

    def save(self) -> bool:
        try:
            payload = self._validated_state(self.to_dict())
            next_generation = self.generation + 1
            self.store.save(payload, next_generation)
            self.generation = next_generation
            self.last_load_source = "primary"
            self.repaired_primary = False
            self.last_error = None
            return True
        except (CheckpointError, OSError, TypeError, ValueError) as exc:
            self.last_error = str(exc)
            return False

    def _load_result(self, result: CheckpointLoadResult) -> bool:
        state = self._validated_state(result.payload)
        self._apply_state(state)
        self.generation = result.generation
        self.last_load_source = result.source
        self.repaired_primary = result.repaired_primary
        self.last_error = None
        return True

    def load(self) -> bool:
        self.last_error = None
        try:
            result = self.store.load()
            try:
                return self._load_result(result)
            except ValueError as primary_error:
                if result.source not in {"primary", "legacy"}:
                    raise
                try:
                    backup = self.store.load_backup()
                    return self._load_result(backup)
                except (CheckpointError, FileNotFoundError, OSError, ValueError) as backup_error:
                    raise ValueError(
                        f"primary and backup save payloads are invalid: {primary_error}; {backup_error}"
                    ) from backup_error
        except FileNotFoundError:
            return False
        except (CheckpointError, OSError, TypeError, ValueError) as exc:
            self.last_error = str(exc)
            return False

    def reset(self) -> None:
        self._reset_values()
        self.generation = 0
        self.last_load_source = None
        self.repaired_primary = False
        self.last_error = None
        self.store.reset()
