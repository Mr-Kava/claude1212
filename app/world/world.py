"""Класс World — главный объект симуляции, держит карту, существ и продвигает время."""

import random
from collections import Counter, defaultdict
from typing import Dict, List

from .map import generate_map
from .tiles import TERRAIN_PROPS, TileType
from .events import maybe_trigger_disaster, Disaster
from ..config import MAP_W, MAP_H


class World:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.tick = 0
        self.w = MAP_W
        self.h = MAP_H
        self.grid = generate_map(seed)
        self.food: List[List[float]] = [
            [TERRAIN_PROPS[self.grid[y][x]].food_cap * 0.6 for x in range(self.w)]
            for y in range(self.h)
        ]
        # Существа создаются и вселяются извне (через app.entities.creature.spawn_initial)
        self.creatures: list = []
        # История
        self.population_history: List[Dict[str, int]] = []
        self.gene_history: Dict[str, list] = defaultdict(list)
        self.disasters: List[Disaster] = []
        self.deaths: Counter = Counter()
        self.births: Counter = Counter()

    # ------- queries -------

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def tile(self, x: int, y: int) -> TileType:
        return self.grid[y][x]

    # ------- step -------

    def step(self):
        """Один тик симуляции."""
        from ..entities.behavior import step_creature
        from ..entities.species import SPECIES
        from ..entities.creature import Creature

        self.tick += 1

        # 1. Активная фаза существ
        for c in list(self.creatures):
            if c.energy <= 0:
                continue
            step_creature(self, c)

        # 2. Сбор мёртвых
        survivors = []
        for c in self.creatures:
            if c.energy <= 0:
                self.deaths[c.species_name] += 1
                continue
            if c.age >= SPECIES[c.species_name].lifespan:
                self.deaths[c.species_name] += 1
                continue
            survivors.append(c)
        self.creatures = survivors

        # 3. Регенерация биомассы
        for y in range(self.h):
            for x in range(self.w):
                props = TERRAIN_PROPS[self.grid[y][x]]
                if self.food[y][x] < props.food_cap:
                    self.food[y][x] = min(props.food_cap, self.food[y][x] + props.regrowth)

        # 4. Возможная катастрофа
        d = maybe_trigger_disaster(self)
        if d is not None:
            self.disasters.append(d)

        # 5. Статистика
        pop = Counter(c.species_name for c in self.creatures)
        self.population_history.append({sp: pop.get(sp, 0) for sp in SPECIES})

        # средние гены
        by_sp = defaultdict(list)
        for c in self.creatures:
            by_sp[c.species_name].append(c.genes())
        for sp_name in SPECIES:
            arr = by_sp.get(sp_name, [])
            if arr:
                avg = {g: round(sum(x[g] for x in arr) / len(arr), 2) for g in arr[0].keys()}
            else:
                avg = {}
            self.gene_history[sp_name].append(avg)
