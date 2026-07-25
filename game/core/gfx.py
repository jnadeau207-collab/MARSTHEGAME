"""
High-quality procedural drawing helpers for STARMAN.
Pure pygame — layered shading, soft glows, bevels, vignette.
"""

import math
import pygame

_glow_cache = {}
_vignette = None


def soft_circle(surface, color, pos, radius, layers=4):
    """Draw a soft radial glow (cached per radius/color)."""
    if radius < 1:
        return
    key = (radius, color[0], color[1], color[2], layers)
    if key not in _glow_cache:
        size = radius * 2 + 4
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for i in range(layers, 0, -1):
            r = max(1, int(radius * i / layers))
            a = int(40 * (i / layers) ** 1.4)
            pygame.draw.circle(s, (*color[:3], a), (cx, cy), r)
        _glow_cache[key] = s
        if len(_glow_cache) > 120:
            _glow_cache.clear()
    img = _glow_cache[key]
    surface.blit(img, (pos[0] - img.get_width() // 2, pos[1] - img.get_height() // 2), special_flags=pygame.BLEND_ALPHA_SDL2)


def soft_circle_additive(surface, color, pos, radius, layers=5):
    if radius < 1:
        return
    key = ("add", radius, color[0], color[1], color[2], layers)
    if key not in _glow_cache:
        size = radius * 2 + 4
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for i in range(layers, 0, -1):
            r = max(1, int(radius * i / layers))
            a = int(55 * (i / layers) ** 1.2)
            pygame.draw.circle(s, (*color[:3], a), (cx, cy), r)
        _glow_cache[key] = s
    img = _glow_cache[key]
    surface.blit(img, (pos[0] - img.get_width() // 2, pos[1] - img.get_height() // 2), special_flags=pygame.BLEND_ADD)


def bevel_rect(surface, rect, base, light=None, dark=None, top_h=5):
    """3D-ish platform: base fill + top highlight + bottom shade + edge."""
    if light is None:
        light = tuple(min(255, c + 50) for c in base)
    if dark is None:
        dark = tuple(max(0, c - 35) for c in base)
    pygame.draw.rect(surface, base, rect)
    th = min(top_h, max(2, rect.h // 3))
    if rect.h > 8:
        pygame.draw.rect(surface, light, (rect.x, rect.y, rect.w, th))
        pygame.draw.rect(surface, dark, (rect.x, rect.bottom - 3, rect.w, 3))
    # left/right subtle
    if rect.w > 10:
        pygame.draw.line(surface, light, (rect.x, rect.y), (rect.x, rect.bottom - 1), 1)
        pygame.draw.line(surface, dark, (rect.right - 1, rect.y), (rect.right - 1, rect.bottom - 1), 1)


def drop_shadow(surface, rect, offset=3, alpha=70):
    s = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, rect.h // 2, rect.w + 2, rect.h // 2 + 2))
    surface.blit(s, (rect.x + offset - 1, rect.y + offset))


def draw_vignette(surface, strength=90):
    global _vignette
    w, h = surface.get_size()
    if _vignette is None or _vignette.get_size() != (w, h):
        _vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_d = math.hypot(cx, cy)
        # sample grid for speed
        step = 4
        for y in range(0, h, step):
            for x in range(0, w, step):
                d = math.hypot(x - cx, y - cy) / max_d
                a = int(strength * max(0, d - 0.35) ** 1.6)
                if a > 2:
                    pygame.draw.rect(_vignette, (0, 0, 0, min(180, a)), (x, y, step, step))
    surface.blit(_vignette, (0, 0))


def gradient_sky(surface, top, bottom, bands=24):
    w, h = surface.get_size()
    for i in range(bands):
        t = i / (bands - 1)
        c = tuple(int(top[j] * (1 - t) + bottom[j] * t) for j in range(3))
        y0 = int(h * i / bands)
        y1 = int(h * (i + 1) / bands)
        pygame.draw.rect(surface, c, (0, y0, w, max(1, y1 - y0)))


def shade(color, amount):
    """amount >0 lighten, <0 darken"""
    return tuple(max(0, min(255, int(c + amount))) for c in color[:3])


def stipple_rect(surface, rect, color, density=0.15):
    """Cheap texture: sparse pixels."""
    import random
    rng = random.Random(rect.x * 31 + rect.y * 17)
    n = max(1, int(rect.w * rect.h * density / 40))
    for _ in range(n):
        px = rect.x + rng.randint(0, max(0, rect.w - 1))
        py = rect.y + rng.randint(0, max(0, rect.h - 1))
        surface.set_at((px % surface.get_width(), py % surface.get_height()), color)
