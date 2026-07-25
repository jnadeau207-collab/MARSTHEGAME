#!/usr/bin/env python3
"""
STARMAN: An Elon Odyssey
A side-scrolling / arena-hybrid narrative action game.
Pure Python + Pygame.
"""

import sys
import os

# Ensure package root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.core.engine import Engine


def main():
    engine = Engine()
    engine.run()


if __name__ == "__main__":
    main()
