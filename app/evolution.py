"""Эволюция: смешивание генов родителей, мутация, ограничения, создание потомка."""

from typing import Optional, TYPE_CHECKING

from .entities.creature import Creature, EVOLVABLE
from .entities.species import SPECIES
from .config import MUTATION_RATE

if TYPE_CHECKING:
    from .world.world import World


GENE_MIN = 0.1
GENE_MAX = 12.0


def make_child(world: "World", a: Creature, b: Creature) -> Optional[Creature]:
    """Создаёт ребёнка от двух родителей того же вида."""
    sp = SPECIES[a.species_name]
    child_genes = {}
    for g in EVOLVABLE:
        avg = (getattr(a, g) + getattr(b, g)) / 2.0
        # лёгкий гауссов дрейф (всегда)
        avg += world.rng.gauss(0, 0.15)
        # шанс крупной мутации
        if world.rng.random() < MUTATION_RATE:
            avg += world.rng.gauss(0, 1.2)
        # ограничение
        avg = max(GENE_MIN, min(GENE_MAX, avg))
        child_genes[g] = round(avg, 2)

    # позиция: рядом с одним из родителей
    nx = max(0, min(world.w - 1, a.x + world.rng.randint(-1, 1)))
    ny = max(0, min(world.h - 1, a.y + world.rng.randint(-1, 1)))
    if world.grid[ny][nx] in sp.forbidden:
        return None

    return Creature(
        species_name=a.species_name,
        x=nx, y=ny,
        speed=child_genes["speed"],
        vision=child_genes["vision"],
        aggression=child_genes["aggression"],
        intellect=child_genes["intellect"],
        stamina=child_genes["stamina"],
        energy=sp.max_energy * 0.5,
        generation=max(a.generation, b.generation) + 1,
    )
