"""HUD — боковая панель со статистикой: популяции, поколения, мутации, события."""

from collections import Counter

import pygame

from ..config import MAP_PX_W, MAP_PX_H, SIDEBAR_PX
from ..entities.species import SPECIES
from . import colors


class HUD:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        try:
            self.font_big = pygame.font.SysFont("DejaVu Sans", 18, bold=True)
            self.font = pygame.font.SysFont("DejaVu Sans", 14)
            self.font_small = pygame.font.SysFont("DejaVu Sans", 12)
        except Exception:
            self.font_big = pygame.font.Font(None, 22)
            self.font = pygame.font.Font(None, 18)
            self.font_small = pygame.font.Font(None, 14)

    # --------------------------------------------------------------------

    def render(self, world, paused: bool, speed_mult: float) -> None:
        x0 = MAP_PX_W
        # фон панели
        pygame.draw.rect(self.surface, colors.PANEL_BG,
                         pygame.Rect(x0, 0, SIDEBAR_PX, MAP_PX_H))
        pygame.draw.line(self.surface, colors.PANEL_BORDER,
                         (x0, 0), (x0, MAP_PX_H), 2)

        y = 10
        # заголовок
        y = self._text(x0 + 10, y, "AETHERIS", self.font_big, colors.ACCENT)
        y = self._text(x0 + 10, y, f"Tick: {world.tick}  Seed: {world.seed}",
                       self.font, colors.TEXT_DIM)
        status = "[PAUSED]" if paused else f"speed x{speed_mult:.1f}"
        y = self._text(x0 + 10, y, status, self.font, colors.TEXT_DIM)
        y += 6

        # популяции
        pop = Counter(c.species_name for c in world.creatures)
        total = sum(pop.values())
        y = self._text(x0 + 10, y, f"Существ: {total}", self.font_big, colors.TEXT)

        for sp_name, sp in SPECIES.items():
            n = pop.get(sp_name, 0)
            # цветной маркер
            pygame.draw.rect(self.surface, sp.color,
                             pygame.Rect(x0 + 10, y + 4, 10, 10))
            line = f"  {sp.symbol} {sp_name:<8} {n:>4}"
            color = colors.TEXT if n > 0 else colors.TEXT_DIM
            self._text(x0 + 26, y, line, self.font, color)
            y += 18

        y += 4
        pygame.draw.line(self.surface, colors.PANEL_BORDER,
                         (x0 + 10, y), (x0 + SIDEBAR_PX - 10, y), 1)
        y += 8

        # поколения и эволюция
        y = self._text(x0 + 10, y, "Поколения:", self.font_big, colors.TEXT)
        max_gen = max((c.generation for c in world.creatures), default=1)
        avg_gen = (
            sum(c.generation for c in world.creatures) / len(world.creatures)
            if world.creatures else 0
        )
        y = self._text(x0 + 10, y, f"  макс {max_gen}  ср {avg_gen:.1f}",
                       self.font, colors.TEXT_DIM)
        y += 4

        # средние гены для самого многочисленного выжившего вида
        if pop:
            top_sp, _ = pop.most_common(1)[0]
            history = world.gene_history.get(top_sp, [])
            if history and history[-1]:
                g = history[-1]
                y = self._text(x0 + 10, y, f"Доминант: {top_sp}",
                               self.font, colors.ACCENT)
                gene_str = (f"spd {g.get('speed',0):.1f}  "
                            f"vis {g.get('vision',0):.1f}  "
                            f"agr {g.get('aggression',0):.1f}")
                y = self._text(x0 + 10, y, gene_str, self.font_small, colors.TEXT_DIM)
                gene_str2 = (f"int {g.get('intellect',0):.1f}  "
                             f"sta {g.get('stamina',0):.1f}")
                y = self._text(x0 + 10, y, gene_str2, self.font_small, colors.TEXT_DIM)

        y += 6
        pygame.draw.line(self.surface, colors.PANEL_BORDER,
                         (x0 + 10, y), (x0 + SIDEBAR_PX - 10, y), 1)
        y += 8

        # рождения
        y = self._text(x0 + 10, y, "Рождений всего:",
                       self.font_big, colors.TEXT)
        births_total = sum(world.births.values())
        y = self._text(x0 + 10, y, f"  {births_total}", self.font, colors.TEXT_DIM)

        # последние катастрофы
        y += 6
        y = self._text(x0 + 10, y, "Катастрофы:", self.font_big, colors.TEXT)
        if world.disasters:
            for d in world.disasters[-4:]:
                y = self._text(x0 + 10, y, f"  t={d.tick}  {d.message}",
                               self.font_small, colors.DISASTER_FLASH)
        else:
            y = self._text(x0 + 10, y, "  пока тихо",
                           self.font_small, colors.TEXT_DIM)

        # подсказки управления внизу
        controls = [
            "[Space] пауза  [↑/↓] скорость",
            "[R] рестарт  [S] сохранить отчёт",
            "[Esc/Q] выход",
        ]
        y = MAP_PX_H - 18 * len(controls) - 6
        for line in controls:
            self._text(x0 + 10, y, line, self.font_small, colors.TEXT_DIM)
            y += 18

    # --------------------------------------------------------------------

    def _text(self, x: int, y: int, s: str, font, color) -> int:
        surf = font.render(s, True, color)
        self.surface.blit(surf, (x, y))
        return y + font.get_linesize()
