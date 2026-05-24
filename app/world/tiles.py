"""Типы тайлов и их свойства."""

from enum import IntEnum
from dataclasses import dataclass


class TileType(IntEnum):
    WATER = 0
    FOREST = 1
    MOUNTAIN = 2
    DESERT = 3
    PLAINS = 4
    TUNDRA = 5
    RESOURCE = 6


@dataclass(frozen=True)
class TerrainProps:
    name: str
    color: tuple                 # RGB для отрисовки
    food_cap: float              # сколько биомассы может быть в клетке
    regrowth: float              # сколько восстанавливается за тик
    drain: float                 # коэффициент расхода энергии на этой клетке


TERRAIN_PROPS = {
    TileType.WATER:    TerrainProps("Вода",    ( 40,  90, 180),  3.0, 0.50, 0.5),
    TileType.FOREST:   TerrainProps("Лес",     ( 30, 110,  40),  9.0, 0.70, 0.3),
    TileType.MOUNTAIN: TerrainProps("Горы",    (130, 130, 130),  1.0, 0.05, 0.7),
    TileType.DESERT:   TerrainProps("Пустыня", (210, 190, 110),  1.0, 0.05, 1.2),
    TileType.PLAINS:   TerrainProps("Равнина", (140, 180,  80),  5.0, 0.40, 0.4),
    TileType.TUNDRA:   TerrainProps("Тундра",  (210, 215, 225),  2.0, 0.10, 1.0),
    TileType.RESOURCE: TerrainProps("Ресурс",  (230, 200,  60), 12.0, 1.00, 0.3),
}
