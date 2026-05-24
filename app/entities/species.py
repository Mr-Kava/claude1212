"""Определения 8 видов существ Aetheris."""

from dataclasses import dataclass, field
from typing import List

from ..world.tiles import TileType


@dataclass(frozen=True)
class Species:
    name: str
    symbol: str
    color: tuple                 # RGB для отрисовки на карте
    diet: str                    # herbivore / carnivore / omnivore / scavenger / detritivore

    # Базовые гены (стартовые)
    speed: float
    vision: float
    aggression: float
    intellect: float
    stamina: float

    preferred: tuple             # tuple[TileType, ...]
    forbidden: tuple             # tuple[TileType, ...]

    start_pop: int
    max_energy: float
    repro_threshold: float
    lifespan: int

    description: str = ""


SPECIES: dict[str, Species] = {
    "Grazor": Species(
        name="Grazor", symbol="G", color=(180, 220, 110), diet="herbivore",
        speed=4, vision=3, aggression=1, intellect=2, stamina=6,
        preferred=(TileType.PLAINS, TileType.FOREST, TileType.RESOURCE),
        forbidden=(TileType.WATER, TileType.MOUNTAIN),
        start_pop=90, max_energy=100, repro_threshold=70, lifespan=60,
        description="Травоядное стадное равнин",
    ),
    "Lupax": Species(
        name="Lupax", symbol="L", color=(220,  60,  60), diet="carnivore",
        speed=6, vision=5, aggression=8, intellect=6, stamina=5,
        preferred=(TileType.FOREST, TileType.PLAINS),
        forbidden=(TileType.WATER, TileType.DESERT),
        start_pop=22, max_energy=120, repro_threshold=95, lifespan=55,
        description="Стайный лесной хищник",
    ),
    "Terrax": Species(
        name="Terrax", symbol="T", color=(120,  80,  40), diet="omnivore",
        speed=2, vision=4, aggression=5, intellect=4, stamina=9,
        preferred=(TileType.MOUNTAIN, TileType.RESOURCE),
        forbidden=(TileType.WATER,),
        start_pop=28, max_energy=150, repro_threshold=110, lifespan=80,
        description="Горный всеядный гигант",
    ),
    "Skywing": Species(
        name="Skywing", symbol="S", color=(240, 240, 240), diet="scavenger",
        speed=8, vision=9, aggression=4, intellect=5, stamina=4,
        preferred=(TileType.MOUNTAIN, TileType.PLAINS, TileType.TUNDRA),
        forbidden=(),
        start_pop=30, max_energy=80, repro_threshold=55, lifespan=45,
        description="Летающий падальщик",
    ),
    "Shakrit": Species(
        name="Shakrit", symbol="K", color=(220, 160,  60), diet="omnivore",
        speed=5, vision=6, aggression=6, intellect=3, stamina=8,
        preferred=(TileType.DESERT, TileType.RESOURCE),
        forbidden=(TileType.WATER, TileType.TUNDRA),
        start_pop=35, max_energy=110, repro_threshold=80, lifespan=50,
        description="Пустынный охотник-собиратель",
    ),
    "Mycor": Species(
        name="Mycor", symbol="M", color=(150,  80, 180), diet="detritivore",
        speed=1, vision=2, aggression=1, intellect=1, stamina=10,
        preferred=(TileType.FOREST, TileType.RESOURCE),
        forbidden=(TileType.WATER, TileType.DESERT),
        start_pop=55, max_energy=90, repro_threshold=45, lifespan=40,
        description="Грибовидный разлагатель",
    ),
    "Aquor": Species(
        name="Aquor", symbol="A", color=( 80, 200, 220), diet="carnivore",
        speed=5, vision=4, aggression=3, intellect=4, stamina=6,
        preferred=(TileType.WATER,),
        forbidden=(TileType.DESERT, TileType.MOUNTAIN, TileType.TUNDRA,
                   TileType.PLAINS, TileType.FOREST, TileType.RESOURCE),
        start_pop=40, max_energy=100, repro_threshold=70, lifespan=50,
        description="Водный хищник",
    ),
    "Cryon": Species(
        name="Cryon", symbol="C", color=(160, 200, 240), diet="omnivore",
        speed=3, vision=4, aggression=4, intellect=5, stamina=9,
        preferred=(TileType.TUNDRA, TileType.MOUNTAIN),
        forbidden=(TileType.DESERT,),
        start_pop=25, max_energy=130, repro_threshold=95, lifespan=65,
        description="Арктический всеядный",
    ),
}
