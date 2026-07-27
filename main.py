#!/usr/bin/env python3
"""MARSTHEGAME Python compatibility runtime entrypoint."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.core.replay_engine import ReplayCapableEngine


def main() -> None:
    engine = ReplayCapableEngine()
    engine.run()


if __name__ == "__main__":
    main()
