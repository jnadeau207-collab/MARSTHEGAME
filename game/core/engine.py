"""Main engine: scene stack, fixed-step loop, and global systems."""

import sys
from copy import deepcopy

import pygame

from game.core.accessibility import normalize_runtime_settings
from game.core.audio import AudioDirector
from game.core.campaign import CAMPAIGN_GRAPH
from game.core.diagnostics import CrashReporter
from game.core.input import InputManager
from game.core.particles import ParticleSystem
from game.core.presentation import PresentationDirector
from game.core.save import SaveData
from game.core.settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE, load_settings, save_settings
from game.core.timing import FixedStepScheduler, FramePlan
from game.scenes.campaign import CampaignScene
from game.scenes.chapter_select import ChapterSelectScene
from game.scenes.credits import CreditsScene
from game.scenes.level import LevelScene
from game.scenes.title import TitleScene
from game.scenes.vertical_slice import VerticalSliceScene


class Engine:
    def __init__(self):
        pygame.init()
        mixer_ready = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22_050, size=-16, channels=2, buffer=512)
            mixer_ready = bool(pygame.mixer.get_init())
        except pygame.error:
            mixer_ready = False

        self.settings = normalize_runtime_settings(load_settings())
        flags = pygame.FULLSCREEN if self.settings.get("fullscreen") else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.timing = FixedStepScheduler(simulation_hz=FPS)
        self.frame_plan = FramePlan(0, 0.0, 0.0, 0.0)
        self.render_alpha = 0.0
        self.running = True
        self.input = InputManager(self.settings.get("keys"))
        self.save = SaveData()
        self.save.load()
        self.particles = ParticleSystem()
        self.audio = AudioDirector(self.settings, enabled=mixer_ready)
        self.presentation = PresentationDirector(self.settings)
        self.scene_stack = []
        self.hit_stop = 0
        self.dt = 1.0
        self.font_sm = pygame.font.SysFont("consolas", 16)
        self.font_md = pygame.font.SysFont("consolas", 24)
        self.font_lg = pygame.font.SysFont("consolas", 40)
        self.font_xl = pygame.font.SysFont("consolas", 56)
        self.diagnostics = CrashReporter()
        self.diagnostics.install(self.diagnostic_context)

        self.push(TitleScene(self))

    def push(self, scene):
        if self.scene_stack:
            self.scene_stack[-1].on_pause()
        self.scene_stack.append(scene)
        scene.on_enter()

    def pop(self):
        if self.scene_stack:
            old = self.scene_stack.pop()
            old.on_exit()
            if self.scene_stack:
                self.scene_stack[-1].on_resume()

    def replace(self, scene):
        while self.scene_stack:
            self.pop()
        self.push(scene)

    def current(self):
        return self.scene_stack[-1] if self.scene_stack else None

    def diagnostic_context(self) -> dict:
        scene = self.current()
        recent_audio = [entry["event"] for entry in list(self.audio.event_log)[-16:]]
        recent_presentation = [entry["name"] for entry in list(self.presentation.event_log)[-16:]]
        return {
            "scene": type(scene).__name__ if scene is not None else None,
            "chapter_id": getattr(scene, "chapter_id", None),
            "slice_id": getattr(scene, "slice_id", None),
            "slice_phase": getattr(scene, "phase", None),
            "campaign_mission": self.save.campaign.get("current_mission"),
            "campaign_revision": self.save.campaign.get("revision"),
            "simulation_steps": self.timing.total_simulation_steps,
            "frame_pacing": self.timing.monitor.snapshot(),
            "audio_state": self.audio.state,
            "recent_audio_events": recent_audio,
            "recent_presentation_events": recent_presentation,
            "save_generation": self.save.generation,
            "save_source": self.save.last_load_source,
            "save_repaired": self.save.repaired_primary,
            "save_error": self.save.last_error,
        }

    def trigger_hit_stop(self, frames=4):
        scaled = self.presentation.hit_stop_frames(frames)
        self.hit_stop = max(self.hit_stop, scaled)

    def _simulate_step(self) -> None:
        self.input.begin_simulation_step()
        try:
            if self.hit_stop > 0:
                self.hit_stop -= 1
                return
            scene = self.current()
            if scene:
                scene.update(1.0)
            self.particles.update()
        finally:
            self.input.end_simulation_step()

    def run(self):
        while self.running:
            elapsed_seconds = self.clock.tick(FPS) / 1000.0
            self.frame_plan = self.timing.plan(elapsed_seconds)
            self.render_alpha = self.frame_plan.interpolation_alpha

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                scene = self.current()
                if scene:
                    scene.handle_event(event)

            self.input.poll_hardware_frame()
            for _ in range(self.frame_plan.simulation_steps):
                self._simulate_step()

            scene = self.current()
            render_dt = min(self.frame_plan.accepted_seconds * FPS, 4.0)
            self.audio.refresh_settings(self.settings)
            self.presentation.refresh_settings(self.settings)
            self.audio.observe(scene)
            self.presentation.observe(scene)
            self.audio.update(render_dt)
            self.presentation.update(render_dt)

            self.screen.fill((8, 8, 12))
            if scene:
                scene.draw(self.screen)
            self.presentation.draw(self.screen)

            if self.settings.get("show_fps"):
                pacing = self.timing.monitor.snapshot()
                text = (
                    f"{int(self.clock.get_fps())} FPS  "
                    f"p95 {pacing['p95_ms']:.1f} ms  "
                    f"hitches {pacing['hitch_count']}"
                )
                fps_txt = self.font_sm.render(text, True, (180, 180, 180))
                self.screen.blit(fps_txt, (SCREEN_WIDTH - fps_txt.get_width() - 8, 8))

            pygame.display.flip()

        save_settings(self.settings)
        self.save.save()
        self.diagnostics.uninstall()
        pygame.quit()
        sys.exit(0)

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
        flags = pygame.FULLSCREEN if self.settings["fullscreen"] else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)

    def start_chapter(self, chapter_id):
        self.save.current_chapter = chapter_id
        self.replace(LevelScene(self, chapter_id))

    def start_campaign_mission(self, mission_id: str) -> None:
        mission = CAMPAIGN_GRAPH.mission(mission_id)
        playable = CAMPAIGN_GRAPH.playable_mission_ids(
            self.save.campaign["completed_missions"]
        )
        if mission_id not in playable:
            raise ValueError(f"campaign mission {mission_id!r} is not currently playable")
        previous_campaign = deepcopy(self.save.campaign)
        self.save.record_campaign_attempt(mission_id)
        if not self.save.save():
            self.save.campaign = previous_campaign
            raise RuntimeError(f"could not persist campaign attempt: {self.save.last_error}")
        if mission["entrypoint"] == "vertical_slice":
            self.replace(VerticalSliceScene(self))
            return
        self.save.campaign = previous_campaign
        self.save.save()
        raise ValueError(f"campaign mission {mission_id!r} has no supported entrypoint")

    def go_campaign(self):
        self.replace(CampaignScene(self))

    def go_vertical_slice(self):
        self.start_campaign_mission("ares_reach")

    def go_title(self):
        self.replace(TitleScene(self))

    def go_chapter_select(self):
        self.replace(ChapterSelectScene(self))

    def go_credits(self):
        self.replace(CreditsScene(self))
