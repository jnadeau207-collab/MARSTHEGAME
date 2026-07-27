"""Campaign navigator layer that authorizes verified Relay Echo replay."""

from __future__ import annotations

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.settings import Colors
from game.data.campaign import MISSION_STATUS_IMPLEMENTED
from game.scenes.campaign import CampaignScene


class ReplayCampaignScene(CampaignScene):
    """Expose completed Relay Echo as REPLAY without widening other mission scope."""

    def _activate(self) -> None:
        mission_id = self.mission_ids[self.selected]
        mission = CAMPAIGN_GRAPH.mission(mission_id)
        campaign = CAMPAIGN_GRAPH.normalize_state(self.engine.save.campaign)
        completed = set(campaign["completed_missions"])
        unlocked = set(campaign["unlocked_missions"])
        if mission_id not in unlocked:
            prerequisites = ", ".join(mission["prerequisites"])
            self.message = f"LOCKED — complete {prerequisites} first"
            self.message_timer = 150
            self.engine.audio.play("ui_move", 0.45)
            return
        if mission_id in completed:
            if mission_id == "relay_echo":
                self.engine.start_campaign_mission(mission_id)
                return
            self.message = "MISSION COMPLETE — REPLAY NOT AUTHORIZED"
            self.message_timer = 210
            self.engine.audio.play("terminal", 0.55)
            return
        if mission["status"] != MISSION_STATUS_IMPLEMENTED:
            self.message = "MISSION AUTHORIZED — CONTENT IN DEVELOPMENT"
            self.message_timer = 180
            self.engine.audio.play("terminal", 0.55)
            return
        self.engine.start_campaign_mission(mission_id)

    def _mission_state(self, mission_id: str) -> tuple[str, tuple[int, int, int]]:
        campaign = CAMPAIGN_GRAPH.normalize_state(self.engine.save.campaign)
        completed = set(campaign["completed_missions"])
        unlocked = set(campaign["unlocked_missions"])
        mission = CAMPAIGN_GRAPH.mission(mission_id)
        if mission_id in completed:
            if mission_id == "relay_echo":
                return "REPLAY", Colors.GOLD
            return "COMPLETE", Colors.SUCCESS
        if mission_id not in unlocked:
            return "LOCKED", (90, 95, 110)
        if mission["status"] == MISSION_STATUS_IMPLEMENTED:
            return "PLAYABLE", Colors.GOLD
        return "PLANNED", Colors.ACCENT
