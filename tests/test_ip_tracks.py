from __future__ import annotations

import unittest

from game.data.ip_tracks import (
    FICTIONALIZED_TRACK,
    REAL_WORLD_TRACK,
    get_chapter_identity,
    get_identity,
    resolve_ip_track,
)


class IpTrackTests(unittest.TestCase):
    def test_both_tracks_cover_all_classic_chapters(self) -> None:
        for track in (REAL_WORLD_TRACK, FICTIONALIZED_TRACK):
            identity = get_identity(track)
            self.assertEqual(set(identity["chapters"]), set(range(1, 9)))
            for chapter in identity["chapters"].values():
                self.assertTrue(chapter["title"])
                self.assertTrue(chapter["level_name"])
                self.assertTrue(chapter["subtitle"])
                self.assertTrue(chapter["description"])

    def test_real_world_track_preserves_current_identity(self) -> None:
        identity = get_identity(REAL_WORLD_TRACK)
        self.assertEqual(identity["game_title"], "STARMAN: An Elon Odyssey")
        self.assertEqual(identity["protagonist"], "Elon")
        self.assertEqual(identity["chapters"][6]["level_name"], "SpaceX Workshop")

    def test_fictionalized_track_removes_named_companies(self) -> None:
        rendered = repr(get_identity(FICTIONALIZED_TRACK))
        for protected_name in ("Elon", "Tesla", "SpaceX", "PayPal", "Zip2"):
            self.assertNotIn(protected_name, rendered)

    def test_invalid_track_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown STARMAN_IP_TRACK"):
            resolve_ip_track("not-a-track")

    def test_unknown_chapter_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown chapter id"):
            get_chapter_identity(9, REAL_WORLD_TRACK)


if __name__ == "__main__":
    unittest.main()
