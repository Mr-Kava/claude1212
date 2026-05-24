"""Класс Creature — конкретная особь со своим набором генов."""

from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING

from .species import SPECIES

if TYPE_CHECKING:
    from ..world.world import World


EVOLVABLE = ("speed", "vision", "aggression", "intellect", "stamina")


@dataclass
class Creature:
    species_name: str
    x: int
    y: int
    # гены (могут отличаться от базовых для вида)
    speed: float
    vision: float
    aggression: float
    intellect: float
    stamina: float
    # состояние
    energy: float
    health: float = 100.0
    age: int = 0
    generation: int = 1

    @property
    def species(self):
        return SPECIES[self.species_name]

    @property
    def diet(self) -> str:
        return self.species.diet

    @property
    def color(self) -> tuple:
        return self.species.color

    def can_enter(self, tile_type) -> bool:
        return tile_type not in self.species.forbidden

    def genes(self) -> Dict[str, float]:
        return {g: getattr(self, g) for g in EVOLVABLE}


def spawn_initial(world: "World") -> None:
    """Раскладывает существ всех видов по карте согласно их предпочтениям."""
    for sp_name, sp in SPECIES.items():
        placed = 0
        attempts = 0
        max_attempts = sp.start_pop * 60
        while placed < sp.start_pop and attempts < max_attempts:
            attempts += 1
            x = world.rng.randint(0, world.w - 1)
            y = world.rng.randint(0, world.h - 1)
            t = world.grid[y][x]
            if t in sp.forbidden:
                continue
            if t not in sp.preferred and world.rng.random() > 0.25:
                continue
            world.creatures.append(Creature(
                species_name=sp_name,
                x=x, y=y,
                speed=sp.speed,
                vision=sp.vision,
                aggression=sp.aggression,
                intellect=sp.intellect,
                stamina=sp.stamina,
                energy=sp.max_energy * 0.7,
            ))
            placed += 1
