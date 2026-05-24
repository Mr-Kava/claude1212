"""Pygame-рендерер карты и существ."""

import pygame

from ..config import TILE_PX, MAP_PX_W, MAP_PX_H
from ..world.tiles import TERRAIN_PROPS
from . import colors


class Renderer:
    """Отвечает за рисование тайлов и существ на экране."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        # Поверхность карты (рисуется один раз при смене seed и кешируется)
        self.map_surface = pygame.Surface((MAP_PX_W, MAP_PX_H))
        self._cached_tick_for_food = -1

    # --------- карта ---------

    def render_map(self, world) -> None:
        """Перерисовывает фон карты целиком."""
        for y in range(world.h):
            for x in range(world.w):
                t = world.grid[y][x]
                base = TERRAIN_PROPS[t].color
                # затемнение пропорционально нехватке пищи (визуализация ресурсов)
                cap = max(0.5, TERRAIN_PROPS[t].food_cap)
                ratio = world.food[y][x] / cap
                ratio = max(0.3, min(1.0, ratio))
                color = tuple(int(b * (0.55 + 0.45 * ratio)) for b in base)
                rect = pygame.Rect(x * TILE_PX, y * TILE_PX, TILE_PX, TILE_PX)
                pygame.draw.rect(self.map_surface, color, rect)

    # --------- существа ---------

    def render_creatures(self, world) -> None:
        """Рисует всех существ как маленькие цветные точки/спрайты."""
        r = max(2, TILE_PX // 3)
        for c in world.creatures:
            cx = c.x * TILE_PX + TILE_PX // 2
            cy = c.y * TILE_PX + TILE_PX // 2
            # тёмная обводка для контраста
            pygame.draw.circle(self.map_surface, (10, 10, 10), (cx, cy), r + 1)
            pygame.draw.circle(self.map_surface, c.color, (cx, cy), r)

    # --------- финальная композиция ---------

    def blit_to_screen(self, x: int = 0, y: int = 0) -> None:
        self.surface.blit(self.map_surface, (x, y))
        # рамка
        pygame.draw.rect(self.surface, colors.PANEL_BORDER,
                         pygame.Rect(x, y, MAP_PX_W, MAP_PX_H), width=1)
