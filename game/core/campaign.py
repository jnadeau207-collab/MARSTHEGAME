"""Validated deterministic campaign graph and progression transactions."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable

from game.data.campaign import (
    CAMPAIGN_ID,
    CAMPAIGN_MISSIONS,
    CAMPAIGN_SCHEMA_VERSION,
    MISSION_STATUS_IMPLEMENTED,
    MISSION_STATUS_PLANNED,
    MISSION_STATUSES,
    START_MISSION_ID,
)

_MISSION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class CampaignDefinitionError(ValueError):
    """Raised when the committed campaign catalog is structurally invalid."""


class CampaignStateError(ValueError):
    """Raised when campaign progression is corrupt or impossible."""


@dataclass(frozen=True)
class CampaignTransition:
    """Deterministic evidence emitted by a campaign progression transaction."""

    event: str
    mission_id: str
    revision: int
    completed_missions: tuple[str, ...]
    unlocked_missions: tuple[str, ...]
    current_mission: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "mission_id": self.mission_id,
            "revision": self.revision,
            "completed_missions": list(self.completed_missions),
            "unlocked_missions": list(self.unlocked_missions),
            "current_mission": self.current_mission,
        }


def validate_campaign_catalog(
    missions: Iterable[dict[str, Any]] = CAMPAIGN_MISSIONS,
    start_mission_id: str = START_MISSION_ID,
) -> list[str]:
    """Return stable validation errors for a campaign mission catalog."""

    errors: list[str] = []
    catalog = list(missions)
    ids: list[str] = []
    sequences: list[int] = []

    for index, mission in enumerate(catalog):
        if not isinstance(mission, dict):
            errors.append(f"mission[{index}] must be an object")
            continue
        mission_id = mission.get("id")
        if not isinstance(mission_id, str) or not _MISSION_ID_PATTERN.fullmatch(mission_id):
            errors.append(f"mission[{index}] has an invalid stable id")
            continue
        ids.append(mission_id)

        sequence = mission.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            errors.append(f"mission {mission_id} sequence must be a positive integer")
        else:
            sequences.append(sequence)

        title = mission.get("title")
        location = mission.get("location")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"mission {mission_id} requires a title")
        if not isinstance(location, str) or not location.strip():
            errors.append(f"mission {mission_id} requires a location")

        status = mission.get("status")
        entrypoint = mission.get("entrypoint")
        if status not in MISSION_STATUSES:
            errors.append(f"mission {mission_id} has unknown status {status!r}")
        elif status == MISSION_STATUS_IMPLEMENTED:
            if not isinstance(entrypoint, str) or not entrypoint:
                errors.append(f"implemented mission {mission_id} requires an entrypoint")
        elif status == MISSION_STATUS_PLANNED and entrypoint is not None:
            errors.append(f"planned mission {mission_id} may not claim a runtime entrypoint")

        prerequisites = mission.get("prerequisites")
        if not isinstance(prerequisites, (tuple, list)):
            errors.append(f"mission {mission_id} prerequisites must be a sequence")
        elif not all(isinstance(item, str) for item in prerequisites):
            errors.append(f"mission {mission_id} prerequisites must contain only mission ids")
        elif len(prerequisites) != len(set(prerequisites)):
            errors.append(f"mission {mission_id} has duplicate prerequisites")

    duplicate_ids = sorted({mission_id for mission_id in ids if ids.count(mission_id) > 1})
    if duplicate_ids:
        errors.append(f"duplicate mission ids: {duplicate_ids}")
    duplicate_sequences = sorted({value for value in sequences if sequences.count(value) > 1})
    if duplicate_sequences:
        errors.append(f"duplicate mission sequences: {duplicate_sequences}")

    known_ids = set(ids)
    if start_mission_id not in known_ids:
        errors.append(f"start mission {start_mission_id!r} is missing")

    prerequisites_by_id: dict[str, tuple[str, ...]] = {}
    for mission in catalog:
        mission_id = mission.get("id") if isinstance(mission, dict) else None
        prerequisites = mission.get("prerequisites") if isinstance(mission, dict) else None
        if mission_id not in known_ids or not isinstance(prerequisites, (tuple, list)):
            continue
        normalized = tuple(item for item in prerequisites if isinstance(item, str))
        prerequisites_by_id[mission_id] = normalized
        for prerequisite in normalized:
            if prerequisite == mission_id:
                errors.append(f"mission {mission_id} may not depend on itself")
            elif prerequisite not in known_ids:
                errors.append(
                    f"mission {mission_id} references missing prerequisite {prerequisite}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(mission_id: str, path: tuple[str, ...]) -> None:
        if mission_id in visited:
            return
        if mission_id in visiting:
            cycle_start = path.index(mission_id) if mission_id in path else 0
            cycle = path[cycle_start:] + (mission_id,)
            errors.append(f"campaign cycle detected: {' -> '.join(cycle)}")
            return
        visiting.add(mission_id)
        for prerequisite in prerequisites_by_id.get(mission_id, ()):
            if prerequisite in known_ids:
                visit(prerequisite, path + (mission_id,))
        visiting.remove(mission_id)
        visited.add(mission_id)

    for mission_id in sorted(known_ids):
        visit(mission_id, ())

    return sorted(set(errors))


class CampaignGraph:
    """Immutable mission graph with validated deterministic progression rules."""

    def __init__(
        self,
        missions: Iterable[dict[str, Any]] = CAMPAIGN_MISSIONS,
        start_mission_id: str = START_MISSION_ID,
    ) -> None:
        catalog = tuple(deepcopy(list(missions)))
        errors = validate_campaign_catalog(catalog, start_mission_id)
        if errors:
            raise CampaignDefinitionError("; ".join(errors))
        self.start_mission_id = start_mission_id
        self._missions = {
            mission["id"]: mission
            for mission in sorted(
                catalog,
                key=lambda item: (item["sequence"], item["id"]),
            )
        }
        self._ordered_ids = tuple(self._missions)

    @property
    def mission_ids(self) -> tuple[str, ...]:
        return self._ordered_ids

    def mission(self, mission_id: str) -> dict[str, Any]:
        try:
            return deepcopy(self._missions[mission_id])
        except KeyError as exc:
            raise CampaignStateError(f"unknown campaign mission {mission_id!r}") from exc

    def unlocked_mission_ids(self, completed: Iterable[str]) -> tuple[str, ...]:
        completed_set = set(completed)
        return tuple(
            mission_id
            for mission_id in self._ordered_ids
            if set(self._missions[mission_id]["prerequisites"]).issubset(completed_set)
        )

    def playable_mission_ids(self, completed: Iterable[str]) -> tuple[str, ...]:
        unlocked = set(self.unlocked_mission_ids(completed))
        return tuple(
            mission_id
            for mission_id in self._ordered_ids
            if mission_id in unlocked
            and self._missions[mission_id]["status"] == MISSION_STATUS_IMPLEMENTED
        )

    def default_state(self) -> dict[str, Any]:
        return {
            "schema_version": CAMPAIGN_SCHEMA_VERSION,
            "campaign_id": CAMPAIGN_ID,
            "revision": 0,
            "current_mission": self.start_mission_id,
            "completed_missions": [],
            "unlocked_missions": list(self.unlocked_mission_ids(())),
            "attempts": {},
        }

    def normalize_state(self, value: Any) -> dict[str, Any]:
        if value is None:
            return self.default_state()
        if not isinstance(value, dict):
            raise CampaignStateError("campaign state must be an object")
        if value.get("schema_version", CAMPAIGN_SCHEMA_VERSION) != CAMPAIGN_SCHEMA_VERSION:
            raise CampaignStateError("campaign state schema version is unsupported")
        if value.get("campaign_id", CAMPAIGN_ID) != CAMPAIGN_ID:
            raise CampaignStateError("campaign state belongs to another campaign")

        revision = value.get("revision", 0)
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise CampaignStateError("campaign revision must be a non-negative integer")

        completed_value = value.get("completed_missions", [])
        if not isinstance(completed_value, list) or not all(
            isinstance(mission_id, str) for mission_id in completed_value
        ):
            raise CampaignStateError("completed_missions must be a string list")
        if len(completed_value) != len(set(completed_value)):
            raise CampaignStateError("completed_missions contains duplicates")
        unknown_completed = sorted(set(completed_value).difference(self._missions))
        if unknown_completed:
            raise CampaignStateError(
                f"completed_missions contains unknown ids: {unknown_completed}"
            )
        completed_set = set(completed_value)
        completed = tuple(
            mission_id for mission_id in self._ordered_ids if mission_id in completed_set
        )
        completed_set = set(completed)
        for mission_id in completed:
            prerequisites = set(self._missions[mission_id]["prerequisites"])
            if not prerequisites.issubset(completed_set):
                missing = sorted(prerequisites.difference(completed_set))
                raise CampaignStateError(
                    f"completed mission {mission_id} is missing prerequisites {missing}"
                )

        unlocked = self.unlocked_mission_ids(completed)
        persisted_unlocked = value.get("unlocked_missions", list(unlocked))
        if not isinstance(persisted_unlocked, list) or not all(
            isinstance(mission_id, str) for mission_id in persisted_unlocked
        ):
            raise CampaignStateError("unlocked_missions must be a string list")
        if set(persisted_unlocked) != set(unlocked):
            raise CampaignStateError("unlocked_missions does not match the campaign graph")

        attempts_value = value.get("attempts", {})
        if not isinstance(attempts_value, dict):
            raise CampaignStateError("campaign attempts must be an object")
        attempts: dict[str, int] = {}
        for mission_id, count in attempts_value.items():
            if mission_id not in self._missions:
                raise CampaignStateError(f"attempts contains unknown mission {mission_id!r}")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise CampaignStateError(f"attempt count for {mission_id} must be non-negative")
            if count:
                attempts[mission_id] = count

        current_mission = value.get("current_mission", self.start_mission_id)
        if current_mission is not None:
            if current_mission not in self._missions:
                raise CampaignStateError("current_mission is unknown")
            if current_mission not in unlocked:
                raise CampaignStateError("current_mission is locked")

        return {
            "schema_version": CAMPAIGN_SCHEMA_VERSION,
            "campaign_id": CAMPAIGN_ID,
            "revision": revision,
            "current_mission": current_mission,
            "completed_missions": list(completed),
            "unlocked_missions": list(unlocked),
            "attempts": attempts,
        }

    def record_attempt(
        self, state: Any, mission_id: str
    ) -> tuple[dict[str, Any], CampaignTransition]:
        normalized = self.normalize_state(state)
        if mission_id not in self.playable_mission_ids(normalized["completed_missions"]):
            raise CampaignStateError(f"mission {mission_id!r} is not currently playable")
        normalized["revision"] += 1
        normalized["current_mission"] = mission_id
        normalized["attempts"][mission_id] = normalized["attempts"].get(mission_id, 0) + 1
        return normalized, self._transition("attempt_started", mission_id, normalized)

    def complete_mission(
        self, state: Any, mission_id: str
    ) -> tuple[dict[str, Any], CampaignTransition]:
        normalized = self.normalize_state(state)
        if mission_id not in self.playable_mission_ids(normalized["completed_missions"]):
            raise CampaignStateError(f"mission {mission_id!r} is not currently playable")
        completed = set(normalized["completed_missions"])
        completed.add(mission_id)
        normalized["completed_missions"] = [item for item in self._ordered_ids if item in completed]
        normalized["unlocked_missions"] = list(
            self.unlocked_mission_ids(normalized["completed_missions"])
        )
        normalized["revision"] += 1
        incomplete_unlocked = [
            item
            for item in normalized["unlocked_missions"]
            if item not in normalized["completed_missions"]
        ]
        normalized["current_mission"] = (
            incomplete_unlocked[0] if incomplete_unlocked else mission_id
        )
        normalized = self.normalize_state(normalized)
        return normalized, self._transition("mission_completed", mission_id, normalized)

    def _transition(
        self,
        event: str,
        mission_id: str,
        state: dict[str, Any],
    ) -> CampaignTransition:
        return CampaignTransition(
            event=event,
            mission_id=mission_id,
            revision=state["revision"],
            completed_missions=tuple(state["completed_missions"]),
            unlocked_missions=tuple(state["unlocked_missions"]),
            current_mission=state["current_mission"],
        )


CAMPAIGN_GRAPH = CampaignGraph()
