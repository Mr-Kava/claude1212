"""Генерация карты 50×50 — слои воды, гор, лесов, пустынь, тундры и ресурсов."""

import random
from typing import List

from .tiles import TileType
from ..config import MAP_W, MAP_H


def generate_map(seed: int = 42) -> List[List[TileType]]:
    """Возвращает MAP_H×MAP_W матрицу TileType."""
    rng = random.Random(seed)
    grid: List[List[TileType]] = [
        [TileType.PLAINS for _ in range(MAP_W)] for _ in range(MAP_H)
    ]

    def stamp(cx: int, cy: int, r: int, t: TileType, overwrite=None):
        for y in range(max(0, cy - r), min(MAP_H, cy + r + 1)):
            for x in range(max(0, cx - r), min(MAP_W, cx + r + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    if overwrite is None or grid[y][x] in overwrite:
                        grid[y][x] = t

    # 1. Водоёмы
    for _ in range(7):
        cx, cy = rng.randint(4, MAP_W - 5), rng.randint(4, MAP_H - 5)
        stamp(cx, cy, rng.randint(3, 7), TileType.WATER)
    # Извилистая река север→юг
    rx, ry = rng.randint(0, MAP_W - 1), 0
    while ry < MAP_H:
        for dx in (-1, 0, 1):
            xx = max(0, min(MAP_W - 1, rx + dx))
            grid[ry][xx] = TileType.WATER
        rx = max(1, min(MAP_W - 2, rx + rng.choice([-1, 0, 0, 1])))
        ry += 1

    # 2. Горные хребты — диагональные линии
    for _ in range(4):
        cx, cy = rng.randint(0, MAP_W - 1), rng.randint(0, MAP_H - 1)
        length = rng.randint(8, 16)
        dx, dy = rng.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
        for i in range(length):
            x, y = cx + dx * i, cy + dy * i
            if 0 <= x < MAP_W and 0 <= y < MAP_H and grid[y][x] != TileType.WATER:
                stamp(x, y, rng.randint(1, 2), TileType.MOUNTAIN, overwrite=[TileType.PLAINS])

    # 3. Леса
    for _ in range(18):
        cx, cy = rng.randint(0, MAP_W - 1), rng.randint(0, MAP_H - 1)
        if grid[cy][cx] == TileType.PLAINS:
            stamp(cx, cy, rng.randint(2, 5), TileType.FOREST, overwrite=[TileType.PLAINS])

    # 4. Пустыни на юге
    for _ in range(5):
        cx = rng.randint(0, MAP_W - 1)
        cy = rng.randint(MAP_H * 3 // 4, MAP_H - 1)
        stamp(cx, cy, rng.randint(4, 7), TileType.DESERT, overwrite=[TileType.PLAINS])

    # 5. Тундра на севере
    for y in range(0, 6):
        for x in range(MAP_W):
            if grid[y][x] == TileType.PLAINS and rng.random() < 0.75:
                grid[y][x] = TileType.TUNDRA

    # 6. Редкие ресурсные зоны
    for _ in range(12):
        x, y = rng.randint(0, MAP_W - 1), rng.randint(0, MAP_H - 1)
        if grid[y][x] in (TileType.PLAINS, TileType.FOREST,
                          TileType.MOUNTAIN, TileType.TUNDRA):
            grid[y][x] = TileType.RESOURCE

    return grid
