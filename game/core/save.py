"""Validated, transactional Classic, slice, and campaign progression state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH, CampaignStateError
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
_DEFAULT_PHASE1_SLICE = {
    "checkpoint_id": 0,
    "failures": 0,
    "best_phase": "arrival",
    "completed": False,
    "resource_gate_open": False,
}
_PHASE1_PHASES = {
    "arrival",
    "movement_mastery",
    "adaptive_combat",
    "failure_recovery",
    "resource_gate",
    "ascent",
    "complete",
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
        self.phase1_slice = dict(_DEFAULT_PHASE1_SLICE)
        self.campaign = CAMPAIGN_GRAPH.default_state()
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

    @classmethod
    def _validated_phase1_slice(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return dict(_DEFAULT_PHASE1_SLICE)
        if not isinstance(value, dict):
            raise ValueError("phase1_slice must be an object")
        checkpoint_id = cls._bounded_int(
            value.get("checkpoint_id", 0),
            0,
            4,
            "phase1_slice.checkpoint_id",
        )
        failures = value.get("failures", 0)
        if isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
            raise ValueError("phase1_slice.failures must be a non-negative integer")
        best_phase = value.get("best_phase", "arrival")
        if best_phase not in _PHASE1_PHASES:
            raise ValueError("phase1_slice.best_phase is unknown")
        completed = value.get("completed", False)
        resource_gate_open = value.get("resource_gate_open", False)
        if not isinstance(completed, bool):
            raise ValueError("phase1_slice.completed must be boolean")
        if not isinstance(resource_gate_open, bool):
            raise ValueError("phase1_slice.resource_gate_open must be boolean")
        if completed and best_phase != "complete":
            raise ValueError("completed Phase 1 slice must have best_phase complete")
        return {
            "checkpoint_id": checkpoint_id,
            "failures": failures,
            "best_phase": best_phase,
            "completed": completed,
            "resource_gate_open": resource_gate_open,
        }

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
        try:
            campaign = CAMPAIGN_GRAPH.normalize_state(data.get("campaign"))
        except CampaignStateError as exc:
            raise ValueError(f"campaign state is invalid: {exc}") from exc
        return {
            "chapter_unlocked": chapter_unlocked,
            "chapter_completed": chapter_completed,
            "current_chapter": current_chapter,
            "unlocks": self._validated_flags(data.get("unlocks")),
            "stats": self._validated_stats(data.get("stats")),
            "phase1_slice": self._validated_phase1_slice(data.get("phase1_slice")),
            "campaign": campaign,
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
        self.phase1_slice = dict(state["phase1_slice"])
        self.campaign = CAMPAIGN_GRAPH.normalize_state(state["campaign"])
        self.settings_volume = state["settings_volume"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter_unlocked": self.chapter_unlocked,
            "chapter_completed": self.chapter_completed,
            "current_chapter": self.current_chapter,
            "unlocks": dict(self.unlocks),
            "stats": dict(self.stats),
            "phase1_slice": dict(self.phase1_slice),
            "campaign": CAMPAIGN_GRAPH.normalize_state(self.campaign),
            "settings_volume": self.settings_volume,
        }

    def from_dict(self, data: Any) -> None:
        self._apply_state(self._validated_state(data))

    def complete_chapter(self, chapter_id: int) -> None:
        chapter_id = self._bounded_int(chapter_id, 1, 8, "chapter_id")
        self.chapter_completed = max(self.chapter_completed, chapter_id)
        self.chapter_unlocked = max(self.chapter_unlocked, chapter_id + 1)

    def update_phase1_slice(
        self,
        *,
        checkpoint_id: int | None = None,
        failures: int | None = None,
        best_phase: str | None = None,
        completed: bool | None = None,
        resource_gate_open: bool | None = None,
    ) -> None:
        candidate = dict(self.phase1_slice)
        updates = {
            "checkpoint_id": checkpoint_id,
            "failures": failures,
            "best_phase": best_phase,
            "completed": completed,
            "resource_gate_open": resource_gate_open,
        }
        for key, value in updates.items():
            if value is not None:
                candidate[key] = value
        self.phase1_slice = self._validated_phase1_slice(candidate)

    def record_campaign_attempt(self, mission_id: str) -> dict[str, Any]:
        self.campaign, transition = CAMPAIGN_GRAPH.record_attempt(self.campaign, mission_id)
        return transition.to_dict()

    def complete_campaign_mission(self, mission_id: str) -> dict[str, Any]:
        self.campaign, transition = CAMPAIGN_GRAPH.complete_mission(self.campaign, mission_id)
        return transition.to_dict()

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
        repaired_primary = result.repaired_primary
        if result.source in {"backup", "backup_legacy"} and not repaired_primary:
            repaired_primary = self.store.repair_primary_from_backup()
        self._apply_state(state)
        self.generation = result.generation
        self.last_load_source = result.source
        self.repaired_primary = repaired_primary
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
                    backup = self.store.load_backup(repair_primary=False)
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
