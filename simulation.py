"""
Aetheris World Simulation
=========================
Полная симуляция мира с эволюцией существ.
Только стандартная библиотека Python (>=3.8). Запуск:

    python3 simulation.py --ticks 300 --seed 42 --out ./output

На выходе: карта мира, графики популяции (ASCII), heatmap ресурсов,
лог поколений, JSON-статистика и текстовый отчёт.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# =============================================================================
# 1. КОНСТАНТЫ МИРА
# =============================================================================

WIDTH = 50
HEIGHT = 50

# Типы ландшафта
WATER = "W"
FOREST = "F"
MOUNTAIN = "M"
DESERT = "D"
PLAINS = "P"
TUNDRA = "T"
RESOURCE = "R"

TERRAINS = [WATER, FOREST, MOUNTAIN, DESERT, PLAINS, TUNDRA, RESOURCE]

TERRAIN_NAME = {
    WATER: "Вода",
    FOREST: "Лес",
    MOUNTAIN: "Горы",
    DESERT: "Пустыня",
    PLAINS: "Равнина",
    TUNDRA: "Тундра",
    RESOURCE: "Богатая зона",
}

# ASCII-символ для карты (моноширинный)
TERRAIN_CHAR = {
    WATER: "~",
    FOREST: "#",
    MOUNTAIN: "^",
    DESERT: ".",
    PLAINS: ",",
    TUNDRA: "*",
    RESOURCE: "$",
}

# Максимум пищи в клетке для каждого типа (восстанавливается каждый тик)
TERRAIN_FOOD_CAP = {
    WATER: 3,
    FOREST: 9,
    MOUNTAIN: 1,
    DESERT: 1,
    PLAINS: 5,
    TUNDRA: 2,
    RESOURCE: 12,

}

# Скорость восстановления пищи
TERRAIN_REGROWTH = {
    WATER: 0.5,
    FOREST: 0.7,
    MOUNTAIN: 0.05,
    DESERT: 0.05,
    PLAINS: 0.4,
    TUNDRA: 0.1,
    RESOURCE: 1.0,
}

# Климатический штраф к энергии за нахождение в этом ландшафте
TERRAIN_DRAIN = {
    WATER: 0.5,
    FOREST: 0.3,
    MOUNTAIN: 0.7,
    DESERT: 1.2,
    PLAINS: 0.4,
    TUNDRA: 1.0,
    RESOURCE: 0.3,
}

GLOBAL_MUTATION_RATE = 0.04   # 4% шанс ощутимой мутации параметра
GLOBAL_DISASTER_CHANCE = 0.012  # шанс катастрофы каждый тик

# =============================================================================
# 2. ВИДЫ СУЩЕСТВ
# =============================================================================

# Поля параметров эволюционируют:
EVOLVABLE = ("speed", "vision", "aggression", "intellect", "stamina")

SPECIES_DEF: Dict[str, dict] = {
    "Grazor": {
        "symbol": "G",
        "speed": 4, "vision": 3, "aggression": 1, "intellect": 2, "stamina": 6,
        "diet": "herbivore",
        "preferred": [PLAINS, FOREST, RESOURCE],
        "forbidden": [WATER, MOUNTAIN],
        "start_pop": 90,
        "max_energy": 100, "repro_threshold": 70,
        "lifespan": 60,
        "ru": "Граzор — травоядное стадное млекопитающее равнин и подлесков.",
    },
    "Lupax": {
        "symbol": "L",
        "speed": 6, "vision": 5, "aggression": 8, "intellect": 6, "stamina": 5,
        "diet": "carnivore",
        "preferred": [FOREST, PLAINS],
        "forbidden": [WATER, DESERT],
        "start_pop": 22,
        "max_energy": 120, "repro_threshold": 95,
        "lifespan": 55,
        "ru": "Люпакс — стайный хищник, охотится на Грaзоров и Майкоров.",
    },
    "Terrax": {
        "symbol": "T",
        "speed": 2, "vision": 4, "aggression": 5, "intellect": 4, "stamina": 9,
        "diet": "omnivore",
        "preferred": [MOUNTAIN, RESOURCE],
        "forbidden": [WATER],
        "start_pop": 28,
        "max_energy": 150, "repro_threshold": 110,
        "lifespan": 80,
        "ru": "Террaкс — горный всеядный гигант, медленный, но очень выносливый.",
    },
    "Skywing": {
        "symbol": "S",
        "speed": 8, "vision": 9, "aggression": 4, "intellect": 5, "stamina": 4,
        "diet": "scavenger",
        "preferred": [MOUNTAIN, PLAINS, TUNDRA],
        "forbidden": [],
        "start_pop": 30,
        "max_energy": 80, "repro_threshold": 55,
        "lifespan": 45,
        "ru": "Скайвинг — летающий падальщик: видит на 9 клеток, но мало энергии.",
    },
    "Shakrit": {
        "symbol": "K",
        "speed": 5, "vision": 6, "aggression": 6, "intellect": 3, "stamina": 8,
        "diet": "omnivore",
        "preferred": [DESERT, RESOURCE],
        "forbidden": [WATER, TUNDRA],
        "start_pop": 35,
        "max_energy": 110, "repro_threshold": 80,
        "lifespan": 50,
        "ru": "Шакрит — пустынный хищник-собиратель, иммунитет к жаре.",
    },
    "Mycor": {
        "symbol": "M",
        "speed": 1, "vision": 2, "aggression": 1, "intellect": 1, "stamina": 10,
        "diet": "detritivore",
        "preferred": [FOREST, RESOURCE],
        "forbidden": [WATER, DESERT],
        "start_pop": 55,
        "max_energy": 90, "repro_threshold": 45,
        "lifespan": 40,
        "ru": "Майкор — грибовидный разлагатель, очень плодовит и почти беззащитен.",
    },
    "Aquor": {
        "symbol": "A",
        "speed": 5, "vision": 4, "aggression": 3, "intellect": 4, "stamina": 6,
        "diet": "carnivore",
        "preferred": [WATER],
        "forbidden": [DESERT, MOUNTAIN, TUNDRA, PLAINS, FOREST, RESOURCE],
        "start_pop": 40,
        "max_energy": 100, "repro_threshold": 70,
        "lifespan": 50,
        "ru": "Аквoр — водный хищник, никогда не выходит на сушу.",
    },
    "Cryon": {
        "symbol": "C",
        "speed": 3, "vision": 4, "aggression": 4, "intellect": 5, "stamina": 9,
        "diet": "omnivore",
        "preferred": [TUNDRA, MOUNTAIN],
        "forbidden": [DESERT],
        "start_pop": 25,
        "max_energy": 130, "repro_threshold": 95,
        "lifespan": 65,
        "ru": "Крайoн — арктический всеядный обитатель тундры и высокогорий.",
    },
}

# =============================================================================
# 3. ГЕНЕРАЦИЯ КАРТЫ
# =============================================================================

def generate_world(seed: int = 42) -> List[List[str]]:
    """Генератор карты 50x50 на основе слоёв (вода → горы → лес → пустыня → тундра → ресурсы)."""
    rng = random.Random(seed)
    grid = [[PLAINS for _ in range(WIDTH)] for _ in range(HEIGHT)]

    def stamp(cx, cy, r, terrain, overwrite_ok=None):
        for y in range(max(0, cy - r), min(HEIGHT, cy + r + 1)):
            for x in range(max(0, cx - r), min(WIDTH, cx + r + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    if overwrite_ok is None or grid[y][x] in overwrite_ok:
                        grid[y][x] = terrain

    # 1. Водоёмы (сначала, чтобы реки и моря определяли остальную географию)
    for _ in range(7):
        cx, cy = rng.randint(4, WIDTH - 5), rng.randint(4, HEIGHT - 5)
        stamp(cx, cy, rng.randint(3, 7), WATER)
    # Длинная река
    rx, ry = rng.randint(0, WIDTH - 1), 0
    while ry < HEIGHT:
        for dx in (-1, 0, 1):
            xx = max(0, min(WIDTH - 1, rx + dx))
            grid[ry][xx] = WATER
        rx = max(1, min(WIDTH - 2, rx + rng.choice([-1, 0, 0, 1])))
        ry += 1

    # 2. Горы (хребты — линии)
    for _ in range(4):
        cx, cy = rng.randint(0, WIDTH - 1), rng.randint(0, HEIGHT - 1)
        length = rng.randint(8, 16)
        dx, dy = rng.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
        for i in range(length):
            x, y = cx + dx * i, cy + dy * i
            if 0 <= x < WIDTH and 0 <= y < HEIGHT and grid[y][x] != WATER:
                stamp(x, y, rng.randint(1, 2), MOUNTAIN, overwrite_ok=[PLAINS])

    # 3. Леса (биомы вокруг водоёмов)
    for _ in range(18):
        cx, cy = rng.randint(0, WIDTH - 1), rng.randint(0, HEIGHT - 1)
        if grid[cy][cx] == PLAINS:
            stamp(cx, cy, rng.randint(2, 5), FOREST, overwrite_ok=[PLAINS])

    # 4. Пустыни — на юге
    for _ in range(5):
        cx = rng.randint(0, WIDTH - 1)
        cy = rng.randint(HEIGHT * 3 // 4, HEIGHT - 1)
        stamp(cx, cy, rng.randint(4, 7), DESERT, overwrite_ok=[PLAINS])

    # 5. Тундра — на севере
    for y in range(0, 6):
        for x in range(WIDTH):
            if grid[y][x] == PLAINS and rng.random() < 0.75:
                grid[y][x] = TUNDRA

    # 6. Богатые зоны (редкие ценные ресурсы)
    for _ in range(12):
        x, y = rng.randint(0, WIDTH - 1), rng.randint(0, HEIGHT - 1)
        if grid[y][x] in (PLAINS, FOREST, MOUNTAIN, TUNDRA):
            grid[y][x] = RESOURCE

    return grid


# =============================================================================
# 4. СУЩЕСТВО
# =============================================================================

@dataclass
class Creature:
    species: str
    x: int
    y: int
    speed: float
    vision: float
    aggression: float
    intellect: float
    stamina: float
    energy: float
    age: int = 0
    generation: int = 1
    parent_genes: dict = field(default_factory=dict)

    @property
    def symbol(self) -> str:
        return SPECIES_DEF[self.species]["symbol"]

    @property
    def diet(self) -> str:
        return SPECIES_DEF[self.species]["diet"]

    @property
    def max_energy(self) -> float:
        return SPECIES_DEF[self.species]["max_energy"]

    @property
    def repro_threshold(self) -> float:
        return SPECIES_DEF[self.species]["repro_threshold"]

    @property
    def lifespan(self) -> int:
        return SPECIES_DEF[self.species]["lifespan"]

    def can_enter(self, terrain: str) -> bool:
        return terrain not in SPECIES_DEF[self.species]["forbidden"]

    def genes(self) -> dict:
        return {k: getattr(self, k) for k in EVOLVABLE}


# =============================================================================
# 5. МИР И СИМУЛЯЦИЯ
# =============================================================================

class World:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.tick = 0
        self.grid = generate_world(seed)
        self.food: List[List[float]] = [
            [TERRAIN_FOOD_CAP[self.grid[y][x]] * 0.6 for x in range(WIDTH)]
            for y in range(HEIGHT)
        ]
        self.creatures: List[Creature] = []
        self.population_history: List[Dict[str, int]] = []
        self.gene_history: Dict[str, List[Dict[str, float]]] = defaultdict(list)
        self.events: List[str] = []
        self.deaths: Counter = Counter()  # cause: count
        self.births_per_species: Counter = Counter()
        self._spawn_initial()

    # -------------------------------------------------------------------------

    def _spawn_initial(self):
        for sp_name, sp in SPECIES_DEF.items():
            placed = 0
            attempts = 0
            while placed < sp["start_pop"] and attempts < sp["start_pop"] * 50:
                attempts += 1
                x = self.rng.randint(0, WIDTH - 1)
                y = self.rng.randint(0, HEIGHT - 1)
                terrain = self.grid[y][x]
                if terrain in sp["forbidden"]:
                    continue
                # bias to preferred
                if terrain not in sp["preferred"] and self.rng.random() > 0.25:
                    continue
                c = Creature(
                    species=sp_name,
                    x=x, y=y,
                    speed=sp["speed"],
                    vision=sp["vision"],
                    aggression=sp["aggression"],
                    intellect=sp["intellect"],
                    stamina=sp["stamina"],
                    energy=sp["max_energy"] * 0.7,
                )
                self.creatures.append(c)
                placed += 1

    # -------------------------------------------------------------------------

    def neighbors(self, x: int, y: int, r: int):
        for yy in range(max(0, y - r), min(HEIGHT, y + r + 1)):
            for xx in range(max(0, x - r), min(WIDTH, x + r + 1)):
                if (xx, yy) != (x, y):
                    yield xx, yy

    def find_prey(self, hunter: Creature) -> Optional[Creature]:
        r = max(1, int(round(hunter.vision)))
        prey_candidates = []
        for c in self.creatures:
            if c is hunter or c.species == hunter.species:
                continue
            if abs(c.x - hunter.x) <= r and abs(c.y - hunter.y) <= r:
                # хищники охотятся в основном на более слабых
                if hunter.diet == "carnivore" and c.diet in ("herbivore", "detritivore", "omnivore"):
                    prey_candidates.append(c)
                elif hunter.diet == "scavenger" and c.energy < 25:
                    prey_candidates.append(c)
                elif hunter.diet == "omnivore" and c.diet in ("herbivore", "detritivore"):
                    if hunter.aggression > 5:
                        prey_candidates.append(c)
        if not prey_candidates:
            return None
        # ближайшая жертва
        prey_candidates.sort(key=lambda c: abs(c.x - hunter.x) + abs(c.y - hunter.y))
        return prey_candidates[0]

    # -------------------------------------------------------------------------

    def step_creature(self, c: Creature):
        terrain = self.grid[c.y][c.x]

        # 1. Метаболизм: тратим энергию пропорционально (10 - stamina) и климату
        drain = (1.5 + (10 - c.stamina) * 0.15) * TERRAIN_DRAIN[terrain]
        c.energy -= drain
        c.age += 1

        # 2. Питание
        if c.diet in ("herbivore", "detritivore"):
            avail = self.food[c.y][c.x]
            bite = min(avail, 4 + c.stamina * 0.3)
            c.energy = min(c.max_energy, c.energy + bite)
            self.food[c.y][c.x] = max(0, avail - bite)
        elif c.diet == "omnivore":
            # сначала пробует растительность, потом охоту
            avail = self.food[c.y][c.x]
            if avail > 0:
                bite = min(avail, 2 + c.stamina * 0.2)
                c.energy = min(c.max_energy, c.energy + bite)
                self.food[c.y][c.x] = max(0, avail - bite)
            if c.energy < c.max_energy * 0.6 and c.aggression > 4:
                prey = self.find_prey(c)
                if prey is not None:
                    self._attempt_kill(c, prey)
        elif c.diet == "carnivore":
            prey = self.find_prey(c)
            if prey is not None:
                self._attempt_kill(c, prey)
        elif c.diet == "scavenger":
            # ест трупов нет, но может добивать раненых
            prey = self.find_prey(c)
            if prey is not None:
                self._attempt_kill(c, prey)
            # плюс подбирает остатки пищи
            avail = self.food[c.y][c.x] * 0.3
            c.energy = min(c.max_energy, c.energy + avail)

        # 3. Движение (с биасом к лучшему соседу)
        self._move(c)

        # 4. Размножение (требует энергии и партнёра рядом)
        if c.energy >= c.repro_threshold and c.age >= 5:
            self._try_reproduce(c)

    def _attempt_kill(self, hunter: Creature, prey: Creature):
        # шанс победы зависит от соотношения скорость+агрессия+интеллект vs скорость+выносливость
        h = hunter.speed + hunter.aggression + hunter.intellect * 0.5
        p = prey.speed + prey.stamina + prey.intellect * 0.3
        chance = h / (h + p)
        if self.rng.random() < chance:
            hunter.energy = min(hunter.max_energy, hunter.energy + min(40, prey.energy * 0.6 + 15))
            prey.energy = -1  # помечаем мёртвым
            self.deaths[f"{prey.species}:hunted_by:{hunter.species}"] += 1

    def _move(self, c: Creature):
        sp = SPECIES_DEF[c.species]
        # ищет в радиусе видимости лучшую клетку
        r = max(1, int(round(c.vision * 0.7)))
        best = (c.x, c.y, -1.0)
        for xx, yy in self.neighbors(c.x, c.y, r):
            terrain = self.grid[yy][xx]
            if terrain in sp["forbidden"]:
                continue
            score = 0.0
            if terrain in sp["preferred"]:
                score += 3.0
            # для травоядных/всеядных — еда важна
            if c.diet in ("herbivore", "detritivore", "omnivore"):
                score += self.food[yy][xx] * 0.4
            dist = abs(xx - c.x) + abs(yy - c.y)
            score -= dist * 0.4
            if score > best[2]:
                best = (xx, yy, score)
        # шанс рандомного движения зависит от интеллекта (тупые двигаются хаотично)
        if self.rng.random() > 0.3 + c.intellect * 0.05:
            # рандомный шаг в пределах скорости
            steps = max(1, int(round(c.speed * 0.4)))
            dx = self.rng.randint(-steps, steps)
            dy = self.rng.randint(-steps, steps)
            nx = max(0, min(WIDTH - 1, c.x + dx))
            ny = max(0, min(HEIGHT - 1, c.y + dy))
            if self.grid[ny][nx] not in sp["forbidden"]:
                c.x, c.y = nx, ny
            return
        # идём к лучшей клетке (но ограничены скоростью)
        steps = max(1, int(round(c.speed * 0.5)))
        dx = max(-steps, min(steps, best[0] - c.x))
        dy = max(-steps, min(steps, best[1] - c.y))
        c.x = max(0, min(WIDTH - 1, c.x + dx))
        c.y = max(0, min(HEIGHT - 1, c.y + dy))

    def _try_reproduce(self, c: Creature):
        # ищем партнёра того же вида в радиусе 2
        partners = [
            o for o in self.creatures
            if o is not c and o.species == c.species
            and abs(o.x - c.x) <= 2 and abs(o.y - c.y) <= 2
            and o.energy >= o.repro_threshold * 0.7
        ]
        if not partners:
            return
        partner = self.rng.choice(partners)
        child = self._make_child(c, partner)
        if child is not None:
            self.creatures.append(child)
            self.births_per_species[c.species] += 1
            c.energy *= 0.55
            partner.energy *= 0.7

    def _make_child(self, a: Creature, b: Creature) -> Optional[Creature]:
        # смешивание генов + мутация
        child_genes = {}
        sp = SPECIES_DEF[a.species]
        for g in EVOLVABLE:
            avg = (getattr(a, g) + getattr(b, g)) / 2.0
            # лёгкий дрейф
            avg += self.rng.gauss(0, 0.15)
            # мутация
            if self.rng.random() < GLOBAL_MUTATION_RATE:
                avg += self.rng.gauss(0, 1.2)
            # ограничения 0..12 (виды могут эволюционировать выше базового максимума)
            avg = max(0.1, min(12.0, avg))
            child_genes[g] = round(avg, 2)
        # ребёнок рождается рядом с одним из родителей
        nx = max(0, min(WIDTH - 1, a.x + self.rng.randint(-1, 1)))
        ny = max(0, min(HEIGHT - 1, a.y + self.rng.randint(-1, 1)))
        if self.grid[ny][nx] in sp["forbidden"]:
            return None
        return Creature(
            species=a.species,
            x=nx, y=ny,
            speed=child_genes["speed"],
            vision=child_genes["vision"],
            aggression=child_genes["aggression"],
            intellect=child_genes["intellect"],
            stamina=child_genes["stamina"],
            energy=a.max_energy * 0.5,
            generation=max(a.generation, b.generation) + 1,
            parent_genes={"a": a.genes(), "b": b.genes()},
        )

    # -------------------------------------------------------------------------

    def _regrow_food(self):
        for y in range(HEIGHT):
            for x in range(WIDTH):
                t = self.grid[y][x]
                cap = TERRAIN_FOOD_CAP[t]
                if self.food[y][x] < cap:
                    self.food[y][x] = min(cap, self.food[y][x] + TERRAIN_REGROWTH[t])

    def _maybe_disaster(self):
        if self.rng.random() > GLOBAL_DISASTER_CHANCE:
            return
        kind = self.rng.choice(["drought", "freeze", "plague", "meteor"])
        if kind == "drought":
            # пустыни и равнины теряют большую часть пищи
            affected = 0
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if self.grid[y][x] in (DESERT, PLAINS):
                        self.food[y][x] *= 0.2
                        affected += 1
            self.events.append(f"t={self.tick}: ЗАСУХА — {affected} клеток пустынь и равнин выгорели")
        elif kind == "freeze":
            # массовая гибель в тундре, штраф к энергии для всех
            killed = 0
            for c in self.creatures:
                if self.grid[c.y][c.x] in (TUNDRA, MOUNTAIN):
                    if self.rng.random() < 0.35 and c.species not in ("Cryon", "Terrax"):
                        c.energy = -1
                        killed += 1
                        self.deaths[f"{c.species}:freeze"] += 1
                else:
                    c.energy -= 8
            self.events.append(f"t={self.tick}: ВЕЛИКИЙ МОРОЗ — погибло {killed} существ в тундре и горах")
        elif kind == "plague":
            # каждое 4-е существо случайно ослабевает
            hit = 0
            for c in self.creatures:
                if self.rng.random() < 0.18:
                    c.energy *= 0.3
                    hit += 1
            self.events.append(f"t={self.tick}: ЭПИДЕМИЯ — {hit} существ ослаблены")
        elif kind == "meteor":
            cx, cy = self.rng.randint(0, WIDTH - 1), self.rng.randint(0, HEIGHT - 1)
            killed = 0
            for c in list(self.creatures):
                if abs(c.x - cx) + abs(c.y - cy) <= 5:
                    c.energy = -1
                    killed += 1
                    self.deaths[f"{c.species}:meteor"] += 1
            for y in range(max(0, cy - 3), min(HEIGHT, cy + 4)):
                for x in range(max(0, cx - 3), min(WIDTH, cx + 4)):
                    self.food[y][x] = 0
            self.events.append(
                f"t={self.tick}: МЕТЕОРИТ упал в ({cx},{cy}) — погибло {killed}, выжжена зона радиусом 5"
            )

    # -------------------------------------------------------------------------

    def step(self):
        self.tick += 1
        # обновляем существ; копия, т.к. список меняется
        for c in list(self.creatures):
            if c.energy <= 0:
                continue
            self.step_creature(c)

        # умирают от голода/старости
        survivors = []
        for c in self.creatures:
            if c.energy <= 0:
                if not any(k.endswith(c.species) for k in self.deaths):
                    self.deaths[f"{c.species}:starvation_or_kill"] += 1
                continue
            if c.age >= c.lifespan:
                self.deaths[f"{c.species}:old_age"] += 1
                continue
            survivors.append(c)
        self.creatures = survivors

        self._regrow_food()
        self._maybe_disaster()

        # статистика
        pop = Counter(c.species for c in self.creatures)
        self.population_history.append({sp: pop.get(sp, 0) for sp in SPECIES_DEF})

        # средние гены по видам
        per_sp = defaultdict(list)
        for c in self.creatures:
            per_sp[c.species].append(c.genes())
        for sp_name in SPECIES_DEF:
            lst = per_sp.get(sp_name, [])
            if lst:
                avg = {g: round(sum(x[g] for x in lst) / len(lst), 2) for g in EVOLVABLE}
            else:
                avg = {g: 0 for g in EVOLVABLE}
            self.gene_history[sp_name].append(avg)

    def run(self, ticks: int, log_every: int = 25, logger=print):
        logger(f"=== Запуск симуляции на {ticks} тиков ===")
        for _ in range(ticks):
            self.step()
            if self.tick % log_every == 0:
                pop = Counter(c.species for c in self.creatures)
                logger(
                    f"t={self.tick:>4}  всего={len(self.creatures):>4}  "
                    + "  ".join(f"{sp}={pop.get(sp,0):>3}" for sp in SPECIES_DEF)
                )
        logger(f"=== Симуляция завершена ===")


# =============================================================================
# 6. ВИЗУАЛИЗАЦИЯ
# =============================================================================

def render_map(grid: List[List[str]], creatures: Optional[List[Creature]] = None,
               show_creatures: bool = True) -> str:
    # копия как символы
    canvas = [[TERRAIN_CHAR[grid[y][x]] for x in range(WIDTH)] for y in range(HEIGHT)]
    if creatures and show_creatures:
        # последний на клетке перекрывает
        for c in creatures:
            canvas[c.y][c.x] = c.symbol
    lines = ["+" + "-" * WIDTH + "+"]
    for row in canvas:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + "-" * WIDTH + "+")
    return "\n".join(lines)


def render_food_heatmap(food: List[List[float]]) -> str:
    chars = " .:-=+*#%@"
    max_food = max(max(row) for row in food) or 1
    lines = ["+" + "-" * WIDTH + "+"]
    for row in food:
        line = []
        for v in row:
            idx = int((v / max_food) * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line.append(chars[idx])
        lines.append("|" + "".join(line) + "|")
    lines.append("+" + "-" * WIDTH + "+")
    lines.append("Шкала: '" + chars + "' (мало → много)")
    return "\n".join(lines)


def render_population_chart(history: List[Dict[str, int]], width: int = 80, height: int = 18) -> str:
    if not history:
        return "(нет данных)"
    species = list(history[0].keys())
    # downsample
    if len(history) > width:
        step = len(history) / width
        sampled = [history[int(i * step)] for i in range(width)]
    else:
        sampled = history
    max_v = max(max(p.values()) for p in sampled) or 1
    # рендерим многострочно: одна строка на 1 вид + общий
    out = []
    out.append(f"Популяции по видам (тиков: {len(history)}, max={max_v})")
    out.append("")
    # общий график (сумма)
    sums = [sum(p.values()) for p in sampled]
    out.append("ОБЩАЯ ПОПУЛЯЦИЯ:")
    out.append(_ascii_lineplot(sums, height // 2, max(sums)))
    out.append("")
    # по видам
    for sp in species:
        series = [p[sp] for p in sampled]
        m = max(series) or 1
        out.append(f"{sp} (max={m}):")
        out.append(_ascii_lineplot(series, 6, m))
    return "\n".join(out)


def _ascii_lineplot(series: List[int], height: int, max_v: int) -> str:
    width = len(series)
    canvas = [[" "] * width for _ in range(height)]
    for x, v in enumerate(series):
        if max_v == 0:
            continue
        h = int((v / max_v) * (height - 1))
        for y in range(h + 1):
            canvas[height - 1 - y][x] = "█" if y == h else "│"
    lines = []
    for row in canvas:
        lines.append("│" + "".join(row) + "│")
    lines.append("└" + "─" * width + "┘")
    return "\n".join(lines)


# =============================================================================
# 7. ОТЧЁТ
# =============================================================================

def build_report(world: World) -> str:
    out = []
    out.append("# Отчёт о симуляции мира Aetheris")
    out.append("")
    out.append(f"Тиков симуляции: **{world.tick}**")
    out.append(f"Всего существ в финале: **{len(world.creatures)}**")
    out.append("")

    # выжившие и вымершие виды
    pop_final = Counter(c.species for c in world.creatures)
    out.append("## Финальные популяции")
    out.append("")
    out.append("| Вид | Старт | Финал | Δ | Статус |")
    out.append("|-----|------:|------:|--:|:------|")
    for sp_name, sp in SPECIES_DEF.items():
        start = sp["start_pop"]
        end = pop_final.get(sp_name, 0)
        delta = end - start
        if end == 0:
            status = "ВЫМЕР"
        elif end < start * 0.3:
            status = "почти вымер"
        elif end > start * 1.5:
            status = "процветает"
        else:
            status = "стабилен"
        out.append(f"| {sp_name} | {start} | {end} | {delta:+d} | {status} |")
    out.append("")

    # причины смерти
    out.append("## Причины смерти")
    out.append("")
    if world.deaths:
        for cause, n in world.deaths.most_common(20):
            out.append(f"- `{cause}` — {n}")
    else:
        out.append("- (нет смертей)")
    out.append("")

    # эволюция генов
    out.append("## Эволюция генов (среднее по виду: старт → финал)")
    out.append("")
    out.append("| Вид | speed | vision | aggression | intellect | stamina |")
    out.append("|-----|-------|--------|------------|-----------|---------|")
    for sp_name, sp in SPECIES_DEF.items():
        gh = world.gene_history.get(sp_name, [])
        if not gh:
            continue
        final_gen = gh[-1] if gh[-1].get("speed", 0) > 0 else (gh[-2] if len(gh) > 1 else gh[-1])
        row = [sp_name]
        for g in EVOLVABLE:
            start_v = sp[g]
            end_v = final_gen[g]
            arrow = "↑" if end_v > start_v + 0.3 else ("↓" if end_v < start_v - 0.3 else "→")
            row.append(f"{start_v}→{end_v}{arrow}")
        out.append("| " + " | ".join(row) + " |")
    out.append("")

    # рождения
    out.append("## Рождаемость (всего за симуляцию)")
    out.append("")
    for sp_name in SPECIES_DEF:
        out.append(f"- {sp_name}: {world.births_per_species[sp_name]} рождений")
    out.append("")

    # события
    out.append("## Катастрофы и события")
    out.append("")
    if world.events:
        for ev in world.events[:50]:
            out.append(f"- {ev}")
    else:
        out.append("- (мир был спокоен)")
    out.append("")

    # анализ
    out.append("## Аналитическое заключение")
    out.append("")
    survivors = [sp for sp, n in pop_final.items() if n > 0]
    extinct = [sp for sp in SPECIES_DEF if sp not in survivors]
    out.append(f"- Выжило видов: **{len(survivors)} из {len(SPECIES_DEF)}**.")
    if extinct:
        out.append(f"- Вымерли: **{', '.join(extinct)}**.")
    else:
        out.append("- Вымерших нет.")
    total = sum(pop_final.values())
    if total:
        top = pop_final.most_common(3)
        out.append(f"- Доминируют: " + ", ".join(f"{sp} ({n})" for sp, n in top) + ".")
    # тренд
    if len(world.population_history) >= 2:
        first = sum(world.population_history[0].values())
        last = sum(world.population_history[-1].values())
        if last > first * 1.2:
            out.append("- Экосистема **расширилась** относительно стартовых условий.")
        elif last < first * 0.6:
            out.append("- Экосистема **схлопывается** — конкуренция за ресурсы и катастрофы оказались жёсткими.")
        else:
            out.append("- Экосистема **в относительном равновесии**.")
    out.append("")
    out.append("## Прогноз")
    out.append("")
    out.append("- Высокая `stamina` и широкая диета (omnivore) — главный предиктор выживания при катастрофах.")
    out.append("- Виды с узкой ландшафтной нишей (Aquor — только вода) уязвимы к локальным засухам/метеоритам.")
    out.append("- Если симуляция продолжится, ожидаемо вырастут `vision` у хищников и `speed` у их жертв (гонка вооружений).")
    out.append("")
    return "\n".join(out)


# =============================================================================
# 8. CLI
# =============================================================================

def main(argv=None):
    p = argparse.ArgumentParser(description="Aetheris world simulation")
    p.add_argument("--ticks", type=int, default=300)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=str, default="./output")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)

    world = World(seed=args.seed)

    # начальная карта
    with open(os.path.join(args.out, "world_map_initial.txt"), "w", encoding="utf-8") as f:
        f.write("ЛЕГЕНДА: ~ вода  # лес  ^ горы  . пустыня  , равнина  * тундра  $ ресурсы\n")
        f.write("Существа: " + "  ".join(f"{sp['symbol']}={name}" for name, sp in SPECIES_DEF.items()) + "\n\n")
        f.write(render_map(world.grid, world.creatures))

    logger = (lambda *a, **kw: None) if args.quiet else print
    world.run(args.ticks, log_every=max(1, args.ticks // 12), logger=logger)

    # финальная карта
    with open(os.path.join(args.out, "world_map_final.txt"), "w", encoding="utf-8") as f:
        f.write(render_map(world.grid, world.creatures))

    # heatmap
    with open(os.path.join(args.out, "food_heatmap.txt"), "w", encoding="utf-8") as f:
        f.write("Heatmap распределения пищи на финальном тике\n\n")
        f.write(render_food_heatmap(world.food))

    # популяции
    with open(os.path.join(args.out, "population_chart.txt"), "w", encoding="utf-8") as f:
        f.write(render_population_chart(world.population_history))

    # JSON статистика
    stats = {
        "ticks": world.tick,
        "seed": args.seed,
        "final_population": Counter(c.species for c in world.creatures),
        "births": dict(world.births_per_species),
        "deaths": dict(world.deaths),
        "events": world.events,
        "population_history": world.population_history,
        "gene_history": dict(world.gene_history),
    }
    # Counter → dict
    stats["final_population"] = dict(stats["final_population"])
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # отчёт
    report = build_report(world)
    with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    if not args.quiet:
        print(f"\nВыходные файлы сохранены в {args.out}/")
        print(" - world_map_initial.txt")
        print(" - world_map_final.txt")
        print(" - food_heatmap.txt")
        print(" - population_chart.txt")
        print(" - stats.json")
        print(" - report.md")


if __name__ == "__main__":
    main()
