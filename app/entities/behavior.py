"""Поведение существ за один тик: метаболизм, питание, охота, движение, размножение."""

from typing import Optional, TYPE_CHECKING

from .species import SPECIES
from .creature import Creature
from ..world.tiles import TERRAIN_PROPS, TileType

if TYPE_CHECKING:
    from ..world.world import World


def step_creature(world: "World", c: Creature) -> None:
    """Главная функция: один шаг жизни существа."""
    sp = c.species
    terrain = world.grid[c.y][c.x]
    props = TERRAIN_PROPS[terrain]

    # 1. Метаболизм — расход энергии (выносливые тратят меньше)
    drain = (1.5 + (10 - c.stamina) * 0.15) * props.drain
    c.energy -= drain
    c.age += 1

    # 2. Питание
    _feed(world, c)

    # 3. Движение
    _move(world, c)

    # 4. Размножение
    if c.energy >= sp.repro_threshold and c.age >= 5:
        _try_reproduce(world, c)


# ----------------------------------------------------------------------- feed

def _feed(world: "World", c: Creature) -> None:
    """Питание в зависимости от диеты."""
    if c.diet in ("herbivore", "detritivore"):
        avail = world.food[c.y][c.x]
        bite = min(avail, 4 + c.stamina * 0.3)
        c.energy = min(c.species.max_energy, c.energy + bite)
        world.food[c.y][c.x] = max(0, avail - bite)
        return

    if c.diet == "omnivore":
        # сначала растения
        avail = world.food[c.y][c.x]
        if avail > 0:
            bite = min(avail, 2 + c.stamina * 0.2)
            c.energy = min(c.species.max_energy, c.energy + bite)
            world.food[c.y][c.x] = max(0, avail - bite)
        # если ещё голоден и агрессивен — охотится
        if c.energy < c.species.max_energy * 0.6 and c.aggression > 4:
            prey = _find_prey(world, c)
            if prey is not None:
                _attempt_kill(world, c, prey)
        return

    if c.diet == "carnivore":
        prey = _find_prey(world, c)
        if prey is not None:
            _attempt_kill(world, c, prey)
        return

    if c.diet == "scavenger":
        prey = _find_prey(world, c)
        if prey is not None:
            _attempt_kill(world, c, prey)
        # подбираем остатки
        avail = world.food[c.y][c.x] * 0.3
        c.energy = min(c.species.max_energy, c.energy + avail)


# --------------------------------------------------------------------- hunt

def _find_prey(world: "World", hunter: Creature) -> Optional[Creature]:
    """Возвращает ближайшую подходящую жертву в радиусе vision."""
    r = max(1, int(round(hunter.vision)))
    candidates = []
    for c in world.creatures:
        if c is hunter or c.species_name == hunter.species_name:
            continue
        if abs(c.x - hunter.x) > r or abs(c.y - hunter.y) > r:
            continue
        if hunter.diet == "carnivore":
            if c.diet in ("herbivore", "detritivore", "omnivore"):
                candidates.append(c)
        elif hunter.diet == "scavenger":
            if c.energy < 25:
                candidates.append(c)
        elif hunter.diet == "omnivore" and hunter.aggression > 5:
            if c.diet in ("herbivore", "detritivore"):
                candidates.append(c)
    if not candidates:
        return None
    candidates.sort(key=lambda c: abs(c.x - hunter.x) + abs(c.y - hunter.y))
    return candidates[0]


def _attempt_kill(world: "World", hunter: Creature, prey: Creature) -> None:
    """Шанс убийства зависит от соотношения атакующих и защитных характеристик."""
    h = hunter.speed + hunter.aggression + hunter.intellect * 0.5
    p = prey.speed + prey.stamina + prey.intellect * 0.3
    chance = h / (h + p)
    if world.rng.random() < chance:
        gain = min(40, prey.energy * 0.6 + 15)
        hunter.energy = min(hunter.species.max_energy, hunter.energy + gain)
        prey.energy = -1  # помечаем как мёртвую


# --------------------------------------------------------------------- move

def _move(world: "World", c: Creature) -> None:
    """Движение с биасом к лучшей клетке. Интеллект снижает рандомность."""
    sp = c.species
    r = max(1, int(round(c.vision * 0.7)))
    best_x, best_y, best_score = c.x, c.y, -1.0
    for yy in range(max(0, c.y - r), min(world.h, c.y + r + 1)):
        for xx in range(max(0, c.x - r), min(world.w, c.x + r + 1)):
            if (xx, yy) == (c.x, c.y):
                continue
            t = world.grid[yy][xx]
            if t in sp.forbidden:
                continue
            score = 0.0
            if t in sp.preferred:
                score += 3.0
            if c.diet in ("herbivore", "detritivore", "omnivore"):
                score += world.food[yy][xx] * 0.4
            dist = abs(xx - c.x) + abs(yy - c.y)
            score -= dist * 0.4
            if score > best_score:
                best_score = score
                best_x, best_y = xx, yy

    # вероятность рандомного хода обратно пропорциональна интеллекту
    if world.rng.random() > 0.3 + c.intellect * 0.05:
        steps = max(1, int(round(c.speed * 0.4)))
        dx = world.rng.randint(-steps, steps)
        dy = world.rng.randint(-steps, steps)
        nx = max(0, min(world.w - 1, c.x + dx))
        ny = max(0, min(world.h - 1, c.y + dy))
        if world.grid[ny][nx] not in sp.forbidden:
            c.x, c.y = nx, ny
        return

    steps = max(1, int(round(c.speed * 0.5)))
    dx = max(-steps, min(steps, best_x - c.x))
    dy = max(-steps, min(steps, best_y - c.y))
    c.x = max(0, min(world.w - 1, c.x + dx))
    c.y = max(0, min(world.h - 1, c.y + dy))


# ---------------------------------------------------------------- reproduce

def _try_reproduce(world: "World", c: Creature) -> None:
    """Ищет партнёра в радиусе 2 и порождает потомка."""
    from ..evolution import make_child

    partners = [
        o for o in world.creatures
        if o is not c and o.species_name == c.species_name
        and abs(o.x - c.x) <= 2 and abs(o.y - c.y) <= 2
        and o.energy >= o.species.repro_threshold * 0.7
    ]
    if not partners:
        return
    partner = world.rng.choice(partners)
    child = make_child(world, c, partner)
    if child is not None:
        world.creatures.append(child)
        world.births[c.species_name] += 1
        c.energy *= 0.55
        partner.energy *= 0.7
