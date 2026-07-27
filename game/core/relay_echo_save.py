"""Replay-capable transactional save envelope for Relay Echo."""

from __future__ import annotations

from typing import Any

from game.core.relay_echo_replay import (
    RelayEchoReplayError,
    default_relay_echo_replay,
    normalize_relay_echo_replay,
)
from game.core.save import SaveData


class RelayEchoSaveData(SaveData):
    """Extend the validated base save with durable Relay Echo run history."""

    def _reset_values(self) -> None:
        super()._reset_values()
        self.relay_echo_replay = default_relay_echo_replay()

    def _validated_state(self, data: Any) -> dict[str, Any]:
        state = super()._validated_state(data)
        try:
            replay = normalize_relay_echo_replay(
                data.get("relay_echo_replay") if isinstance(data, dict) else None
            )
        except RelayEchoReplayError as exc:
            raise ValueError(f"Relay Echo replay archive is invalid: {exc}") from exc
        if replay["completed_runs"] and "relay_echo" not in state["campaign"]["completed_missions"]:
            raise ValueError("Relay Echo archived runs require durable campaign completion")
        state["relay_echo_replay"] = replay
        return state

    def _apply_state(self, state: dict[str, Any]) -> None:
        super()._apply_state(state)
        self.relay_echo_replay = normalize_relay_echo_replay(state.get("relay_echo_replay"))

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["relay_echo_replay"] = normalize_relay_echo_replay(self.relay_echo_replay)
        return payload
