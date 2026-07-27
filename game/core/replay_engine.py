"""Replay-capable Python compatibility engine for completed Relay Echo runs."""

from __future__ import annotations

from copy import deepcopy

from game.core.engine import Engine
from game.core.relay_echo_replay import prepare_relay_echo_replay
from game.core.relay_echo_save import RelayEchoSaveData
from game.scenes.campaign_replay import ReplayCampaignScene
from game.scenes.relay_echo_promoted import PromotedRelayEchoScene


class ReplayCapableEngine(Engine):
    """Preserve the validated prototype engine while adding replay persistence."""

    def __init__(self) -> None:
        super().__init__()
        save_path = self.save.path
        self.save = RelayEchoSaveData(save_path)
        self.save.load()

    def start_campaign_mission(self, mission_id: str) -> None:
        completed = set(self.save.campaign["completed_missions"])
        if mission_id != "relay_echo" or mission_id not in completed:
            super().start_campaign_mission(mission_id)
            return

        previous_campaign = deepcopy(self.save.campaign)
        previous_relay = deepcopy(self.save.relay_echo)
        previous_archive = deepcopy(self.save.relay_echo_replay)
        prepare_relay_echo_replay(self.save)
        if not self.save.save():
            self.save.campaign = previous_campaign
            self.save.relay_echo = previous_relay
            self.save.relay_echo_replay = previous_archive
            raise RuntimeError(f"could not persist Relay Echo replay: {self.save.last_error}")
        self.replace(PromotedRelayEchoScene(self))

    def go_campaign(self) -> None:
        self.replace(ReplayCampaignScene(self))
