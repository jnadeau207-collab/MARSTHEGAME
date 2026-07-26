"""Campaign-promoted Relay Echo scene with atomic campaign completion."""

from __future__ import annotations

from copy import deepcopy

from game.core.relay_echo_promotion import complete_relay_echo_campaign
from game.scenes.relay_echo_accessible import AccessibleRelayEchoScene


class PromotedRelayEchoScene(AccessibleRelayEchoScene):
    """Expose Relay Echo through the campaign and commit its successor atomically."""

    slice_id = "relay_echo_campaign_mission"

    def _persist_objective(
        self,
        objective_id: str,
        evidence: dict | None = None,
    ) -> bool:
        if objective_id != "extract_before_collapse":
            return super()._persist_objective(objective_id, evidence)

        previous_relay = deepcopy(self.engine.save.relay_echo)
        previous_campaign = deepcopy(self.engine.save.campaign)
        transition = complete_relay_echo_campaign(
            self.engine.save,
            evidence,
        )
        if not self.engine.save.save():
            self.engine.save.relay_echo = previous_relay
            self.engine.save.campaign = previous_campaign
            self.msg = f"Mission completion failed to persist: {self.engine.save.last_error}"
            self.msg_timer = 240
            return False

        self._last_transition = transition
        self.phase = self.mission_state["current_state"]
        self.msg = "Extraction complete — Phobos Vector authorized"
        self.msg_timer = 240
        self.mission_complete = True
        self.completion_timer = 0.0
        self.player.invuln = 10_000
        self.engine.presentation.set_cinematic(not self.accessibility.reduced_motion)
        self.engine.presentation.cue("goal", 1.3)
        self.engine.audio.play("goal", 1.2)
        return True
