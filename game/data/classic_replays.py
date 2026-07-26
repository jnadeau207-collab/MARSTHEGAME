"""Version-controlled deterministic input tracks for Classic Mode regression.

Tracks are run-length encoded as ``(frame_count, active_actions)`` segments. They
exercise the production input manager and player controller before the existing
lifecycle completion check verifies save and scene transitions.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from typing import Final

ReplaySegment = tuple[int, tuple[str, ...]]
ReplayTrack = tuple[ReplaySegment, ...]

_GROUND_ROUTE: Final[ReplayTrack] = (
    (12, ("right",)),
    (1, ("right", "jump")),
    (11, ("right", "jump")),
    (18, ("right",)),
    (1, ("right", "dash")),
    (16, ("right",)),
    (1, ("right", "attack")),
    (14, ("right",)),
    (1, ("right", "jump")),
    (9, ("right", "jump")),
    (18, ("right",)),
    (1, ("interact",)),
    (8, ()),
)

_ASCENT_ROUTE: Final[ReplayTrack] = (
    (8, ("right",)),
    (1, ("right", "jump")),
    (10, ("right", "jump")),
    (6, ("left",)),
    (1, ("left", "jump")),
    (9, ("left", "jump")),
    (8, ("right",)),
    (1, ("right", "dash")),
    (14, ("right",)),
    (1, ("right", "jump")),
    (8, ("right", "jump")),
    (1, ("right", "jump")),
    (8, ("right", "jump")),
    (1, ("attack",)),
    (1, ("interact",)),
    (8, ()),
)

CLASSIC_INPUT_TRACKS: Final[dict[int, ReplayTrack]] = {
    1: _GROUND_ROUTE,
    2: _GROUND_ROUTE,
    3: _GROUND_ROUTE,
    4: _GROUND_ROUTE,
    5: _GROUND_ROUTE,
    6: _GROUND_ROUTE,
    7: _ASCENT_ROUTE,
    8: _GROUND_ROUTE,
}


def expand_track(track: ReplayTrack) -> Iterator[frozenset[str]]:
    """Yield one immutable action set for every recorded frame."""

    for frame_count, actions in track:
        if frame_count <= 0:
            raise ValueError(f"Replay segment frame count must be positive: {frame_count}")
        frame = frozenset(actions)
        for _ in range(frame_count):
            yield frame


def track_digest(track: ReplayTrack) -> str:
    """Return a stable digest so CI evidence identifies the exact recording."""

    serialized = json.dumps(track, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
