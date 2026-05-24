"""Природные катастрофы — засуха, мороз, эпидемия, метеорит."""

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .tiles import TileType

if TYPE_CHECKING:
    from .world import World


@dataclass
class Disaster:
    tick: int
    kind: str
    message: str


def maybe_trigger_disaster(world: "World") -> Disaster | None:
    """С вероятностью DISASTER_CHANCE случается одно из 4 событий."""
    from ..config import DISASTER_CHANCE
    if world.rng.random() > DISASTER_CHANCE:
        return None

    kind = world.rng.choice(["drought", "freeze", "plague", "meteor"])

    if kind == "drought":
        affected = 0
        for y in range(world.h):
            for x in range(world.w):
                if world.grid[y][x] in (TileType.DESERT, TileType.PLAINS):
                    world.food[y][x] *= 0.2
                    affected += 1
        msg = f"ЗАСУХА — выгорели {affected} клеток"

    elif kind == "freeze":
        killed = 0
        for c in world.creatures:
            t = world.grid[c.y][c.x]
            if t in (TileType.TUNDRA, TileType.MOUNTAIN):
                if c.species_name not in ("Cryon", "Terrax") and world.rng.random() < 0.35:
                    c.energy = -1
                    killed += 1
            else:
                c.energy -= 8
        msg = f"ВЕЛИКИЙ МОРОЗ — погибло {killed}"

    elif kind == "plague":
        hit = 0
        for c in world.creatures:
            if world.rng.random() < 0.18:
                c.energy *= 0.3
                hit += 1
        msg = f"ЭПИДЕМИЯ — ослаблено {hit}"

    else:  # meteor
        cx = world.rng.randint(0, world.w - 1)
        cy = world.rng.randint(0, world.h - 1)
        killed = 0
        for c in world.creatures:
            if abs(c.x - cx) + abs(c.y - cy) <= 5:
                c.energy = -1
                killed += 1
        for y in range(max(0, cy - 3), min(world.h, cy + 4)):
            for x in range(max(0, cx - 3), min(world.w, cx + 4)):
                world.food[y][x] = 0
        msg = f"МЕТЕОРИТ в ({cx},{cy}) — погибло {killed}"

    return Disaster(tick=world.tick, kind=kind, message=msg)
