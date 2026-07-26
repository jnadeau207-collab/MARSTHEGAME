"""Stable fictionalized campaign mission definitions for Phase 2."""

from __future__ import annotations

from typing import Final

CAMPAIGN_SCHEMA_VERSION: Final = 1
CAMPAIGN_ID: Final = "frontier_campaign"
START_MISSION_ID: Final = "ares_reach"

MISSION_STATUS_IMPLEMENTED: Final = "implemented"
MISSION_STATUS_PLANNED: Final = "planned"
MISSION_STATUSES: Final = frozenset(
    {
        MISSION_STATUS_IMPLEMENTED,
        MISSION_STATUS_PLANNED,
    }
)

CAMPAIGN_MISSIONS: Final = (
    {
        "id": "ares_reach",
        "sequence": 1,
        "title": "Ares Reach: First Descent",
        "location": "Mars — Ares Reach",
        "status": MISSION_STATUS_IMPLEMENTED,
        "entrypoint": "vertical_slice",
        "contract": None,
        "prerequisites": (),
        "design_pillars": (
            "mythic_kinetic_earnestness",
            "player_agency_through_mastery",
            "accessibility_first_feel",
        ),
    },
    {
        "id": "relay_echo",
        "sequence": 2,
        "title": "Relay Echo",
        "location": "Mars — Noctis Relay",
        "status": MISSION_STATUS_PLANNED,
        "entrypoint": None,
        "contract": "relay_echo",
        "prerequisites": ("ares_reach",),
        "design_pillars": (
            "player_agency_through_mastery",
            "procedural_authored_hybrid",
        ),
    },
    {
        "id": "phobos_vector",
        "sequence": 3,
        "title": "Phobos Vector",
        "location": "Mars Orbit — Phobos Transfer",
        "status": MISSION_STATUS_PLANNED,
        "entrypoint": None,
        "contract": None,
        "prerequisites": ("relay_echo",),
        "design_pillars": (
            "multiplanetary_progression",
            "mythic_kinetic_earnestness",
        ),
    },
    {
        "id": "frontier_burn",
        "sequence": 4,
        "title": "Frontier Burn",
        "location": "Interplanetary Transfer",
        "status": MISSION_STATUS_PLANNED,
        "entrypoint": None,
        "contract": None,
        "prerequisites": ("phobos_vector",),
        "design_pillars": (
            "multiplanetary_progression",
            "procedural_authored_hybrid",
        ),
    },
)
