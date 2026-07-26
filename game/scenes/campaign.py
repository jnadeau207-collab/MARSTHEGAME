"""Phase 2 campaign navigator with truthful implemented/planned mission states."""

from __future__ import annotations

import pygame

from game.core import gfx
from game.core.campaign import CAMPAIGN_GRAPH
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from game.data.campaign import MISSION_STATUS_IMPLEMENTED
from game.scenes.base import Scene


class CampaignScene(Scene):
    """Expose campaign progression without presenting planned missions as playable."""

    def __init__(self, engine) -> None:
        super().__init__(engine)
        self.selected = 0
        self.mission_ids = list(CAMPAIGN_GRAPH.mission_ids)
        self.message = ""
        self.message_timer = 0.0
        self.timer = 0.0

    def on_enter(self) -> None:
        self.engine.save.load()
        current = self.engine.save.campaign.get("current_mission")
        if current in self.mission_ids:
            self.selected = self.mission_ids.index(current)
        self.message = ""
        self.message_timer = 0.0

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.engine.go_title()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self._move(-1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._move(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate()

    def update(self, dt) -> None:
        self.timer += dt
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
        inp = self.engine.input
        if inp.just_pressed("up"):
            self._move(-1)
        if inp.just_pressed("down"):
            self._move(1)
        if inp.just_pressed("confirm") or inp.just_pressed("jump"):
            self._activate()
        if inp.just_pressed("back") or inp.just_pressed("pause"):
            self.engine.go_title()

    def _move(self, direction: int) -> None:
        self.selected = (self.selected + direction) % len(self.mission_ids)
        self.engine.audio.play("ui_move", 0.65)
        self.engine.presentation.cue("ui_move", 0.45)

    def _activate(self) -> None:
        mission_id = self.mission_ids[self.selected]
        mission = CAMPAIGN_GRAPH.mission(mission_id)
        campaign = CAMPAIGN_GRAPH.normalize_state(self.engine.save.campaign)
        unlocked = set(campaign["unlocked_missions"])
        if mission_id not in unlocked:
            prerequisites = ", ".join(mission["prerequisites"])
            self.message = f"LOCKED — complete {prerequisites} first"
            self.message_timer = 150
            self.engine.audio.play("ui_move", 0.45)
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
            return "COMPLETE", Colors.SUCCESS
        if mission_id not in unlocked:
            return "LOCKED", (90, 95, 110)
        if mission["status"] == MISSION_STATUS_IMPLEMENTED:
            return "PLAYABLE", Colors.GOLD
        return "PLANNED", Colors.ACCENT

    def draw(self, surface) -> None:
        gfx.gradient_sky(surface, (7, 9, 20), (35, 13, 18), bands=32)
        mars_center = (SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2)
        gfx.soft_circle(surface, (130, 48, 28), mars_center, 125, layers=6)
        pygame.draw.circle(surface, (156, 62, 34), mars_center, 82)
        pygame.draw.circle(
            surface,
            (92, 32, 23),
            (mars_center[0] - 26, mars_center[1] + 10),
            24,
        )

        title = self.engine.font_xl.render("FRONTIER CAMPAIGN", True, Colors.WHITE)
        surface.blit(title, (70, 54))
        subtitle = self.engine.font_sm.render(
            "Implemented missions are playable. Planned missions are never presented as finished.",
            True,
            (145, 155, 175),
        )
        surface.blit(subtitle, (74, 116))

        start_y = 175
        for index, mission_id in enumerate(self.mission_ids):
            mission = CAMPAIGN_GRAPH.mission(mission_id)
            selected = index == self.selected
            y = start_y + index * 88
            panel = pygame.Surface((720, 72), pygame.SRCALPHA)
            panel.fill((8, 10, 18, 205 if selected else 150))
            border = Colors.ACCENT if selected else (55, 62, 80)
            pygame.draw.rect(panel, border, panel.get_rect(), 2 if selected else 1, 6)
            surface.blit(panel, (70, y))

            state, state_color = self._mission_state(mission_id)
            sequence = self.engine.font_sm.render(
                f"MISSION {mission['sequence']:02d}", True, (115, 130, 155)
            )
            name = self.engine.font_md.render(mission["title"], True, Colors.WHITE)
            location = self.engine.font_sm.render(
                mission["location"], True, (155, 160, 175)
            )
            badge = self.engine.font_sm.render(state, True, state_color)
            surface.blit(sequence, (90, y + 10))
            surface.blit(name, (90, y + 28))
            surface.blit(location, (385, y + 33))
            surface.blit(badge, (700, y + 28))

        campaign = CAMPAIGN_GRAPH.normalize_state(self.engine.save.campaign)
        progress = self.engine.font_sm.render(
            f"Campaign revision {campaign['revision']}  ·  "
            f"Completed {len(campaign['completed_missions'])}/{len(self.mission_ids)}",
            True,
            (130, 145, 165),
        )
        surface.blit(progress, (74, SCREEN_HEIGHT - 76))
        footer = self.engine.font_sm.render(
            "W/S or arrows select  ·  Enter launch  ·  Esc return",
            True,
            (110, 120, 140),
        )
        surface.blit(footer, (74, SCREEN_HEIGHT - 46))

        if self.message_timer > 0 and self.message:
            text = self.engine.font_md.render(self.message, True, Colors.GOLD)
            background = pygame.Surface(
                (text.get_width() + 32, text.get_height() + 18), pygame.SRCALPHA
            )
            background.fill((0, 0, 0, 210))
            pygame.draw.rect(background, Colors.GOLD, background.get_rect(), 1, 5)
            x = SCREEN_WIDTH // 2 - background.get_width() // 2
            surface.blit(background, (x, SCREEN_HEIGHT - 135))
            surface.blit(text, (x + 16, SCREEN_HEIGHT - 126))

        gfx.draw_vignette(surface, strength=90)
