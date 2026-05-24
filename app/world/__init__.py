"""Подсистема мира: тайлы, генерация карты, природные катастрофы."""
from .tiles import TileType, TERRAIN_PROPS
from .map import generate_map
from .world import World
from .events import Disaster

__all__ = ["TileType", "TERRAIN_PROPS", "generate_map", "World", "Disaster"]
