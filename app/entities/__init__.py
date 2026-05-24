"""Подсистема существ: виды, объекты и поведение."""
from .species import SPECIES, Species
from .creature import Creature, spawn_initial
from .behavior import step_creature

__all__ = ["SPECIES", "Species", "Creature", "spawn_initial", "step_creature"]
