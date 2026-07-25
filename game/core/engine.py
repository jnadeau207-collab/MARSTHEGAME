"""
Main engine: scene stack, game loop, global systems.
"""

import pygame
import sys
from game.core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, load_settings, save_settings
)
from game.core.input import InputManager
from game.core.save import SaveData
from game.core.particles import ParticleSystem
from game.scenes.title import TitleScene
from game.scenes.chapter_select import ChapterSelectScene
from game.scenes.level import LevelScene
from game.scenes.credits import CreditsScene


class Engine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.settings = load_settings()
        flags = pygame.FULLSCREEN if self.settings.get("fullscreen") else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.input = InputManager(self.settings.get("keys"))
        self.save = SaveData()
        self.save.load()
        self.particles = ParticleSystem()
        self.scene_stack = []
        self.hit_stop = 0
        self.dt = 1.0
        self.font_sm = pygame.font.SysFont("consolas", 16)
        self.font_md = pygame.font.SysFont("consolas", 24)
        self.font_lg = pygame.font.SysFont("consolas", 40)
        self.font_xl = pygame.font.SysFont("consolas", 56)

        # Start at title
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

    def trigger_hit_stop(self, frames=4):
        self.hit_stop = max(self.hit_stop, frames)

    def run(self):
        while self.running:
            raw_dt = self.clock.tick(FPS) / 1000.0
            self.dt = min(raw_dt * 60.0, 2.0)  # frame-normalized, capped

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                scene = self.current()
                if scene:
                    scene.handle_event(event)

            self.input.update()

            if self.hit_stop > 0:
                self.hit_stop -= 1
            else:
                scene = self.current()
                if scene:
                    scene.update(self.dt)
                self.particles.update()

            # Draw
            self.screen.fill((8, 8, 12))
            scene = self.current()
            if scene:
                scene.draw(self.screen)

            if self.settings.get("show_fps"):
                fps_txt = self.font_sm.render(f"{int(self.clock.get_fps())}", True, (180, 180, 180))
                self.screen.blit(fps_txt, (SCREEN_WIDTH - 40, 8))

            pygame.display.flip()

        save_settings(self.settings)
        self.save.save()
        pygame.quit()
        sys.exit(0)

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
        flags = pygame.FULLSCREEN if self.settings["fullscreen"] else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)

    def start_chapter(self, chapter_id):
        self.save.current_chapter = chapter_id
        self.replace(LevelScene(self, chapter_id))

    def go_title(self):
        self.replace(TitleScene(self))

    def go_chapter_select(self):
        self.replace(ChapterSelectScene(self))

    def go_credits(self):
        self.replace(CreditsScene(self))
