"""
Base scene interface.
"""


class Scene:
    def __init__(self, engine):
        self.engine = engine

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def on_pause(self):
        pass

    def on_resume(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass
