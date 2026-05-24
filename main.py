"""
Aetheris — настольное приложение-симуляция мира с эволюцией существ.

Запуск с GUI (pygame):
    python3 main.py
    python3 main.py --seed 7 --tps 10

Запуск без GUI для проверки логики (на машинах без pygame):
    python3 main.py --headless --ticks 200

Управление в окне:
    Space     — пауза / продолжить
    ↑ / ↓     — увеличить / уменьшить скорость симуляции
    R         — рестарт с новым случайным seed
    S         — сохранить статистику и отчёт в ./output_app/
    Esc / Q   — выйти
"""

import argparse
import json
import os
import random
import sys
from collections import Counter

from app.config import (
    WINDOW_W, WINDOW_H, MAP_PX_W, MAP_PX_H,
    FPS, TICKS_PER_SECOND, SEED_DEFAULT,
)
from app.world.world import World
from app.entities.creature import spawn_initial
from app.entities.species import SPECIES


# -----------------------------------------------------------------------------
# Headless-режим: без GUI, только тики и сохранение отчёта
# -----------------------------------------------------------------------------

def run_headless(seed: int, ticks: int, out_dir: str) -> None:
    print(f"=== Headless run: seed={seed}, ticks={ticks} ===")
    world = World(seed=seed)
    spawn_initial(world)
    log_every = max(1, ticks // 12)
    for _ in range(ticks):
        world.step()
        if world.tick % log_every == 0:
            pop = Counter(c.species_name for c in world.creatures)
            print(f"t={world.tick:>4} total={len(world.creatures):>4} "
                  + " ".join(f"{SPECIES[sp].symbol}={pop.get(sp,0):>3}" for sp in SPECIES))
    _save_report(world, out_dir)
    print(f"Отчёт сохранён в {out_dir}/")


# -----------------------------------------------------------------------------
# GUI-режим: pygame
# -----------------------------------------------------------------------------

def run_gui(seed: int, tps: float) -> None:
    try:
        import pygame
    except ImportError:
        print("ОШИБКА: библиотека pygame не установлена.")
        print("Установи её командой:  python3 -m pip install pygame")
        print("Или запусти без GUI:    python3 main.py --headless")
        sys.exit(1)

    from app.ui.renderer import Renderer
    from app.ui.hud import HUD
    from app.ui import colors

    pygame.init()
    pygame.display.set_caption("Aetheris — World Simulation")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()

    world = World(seed=seed)
    spawn_initial(world)

    renderer = Renderer(screen)
    hud = HUD(screen)

    paused = False
    speed_mult = 1.0
    frames_per_tick = max(1, int(FPS / (TICKS_PER_SECOND * speed_mult)))
    frame_counter = 0

    running = True
    while running:
        # ---------------- ввод ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    speed_mult = min(8.0, speed_mult * 1.5)
                    frames_per_tick = max(1, int(FPS / (TICKS_PER_SECOND * speed_mult)))
                elif event.key == pygame.K_DOWN:
                    speed_mult = max(0.25, speed_mult / 1.5)
                    frames_per_tick = max(1, int(FPS / (TICKS_PER_SECOND * speed_mult)))
                elif event.key == pygame.K_r:
                    new_seed = random.randint(0, 100000)
                    world = World(seed=new_seed)
                    spawn_initial(world)
                    print(f"[restart] new seed = {new_seed}")
                elif event.key == pygame.K_s:
                    out_dir = "./output_app"
                    _save_report(world, out_dir)
                    print(f"[save] отчёт сохранён в {out_dir}/")

        # ---------------- обновление мира ----------------
        if not paused:
            frame_counter += 1
            if frame_counter >= frames_per_tick:
                frame_counter = 0
                world.step()

        # ---------------- отрисовка ----------------
        screen.fill(colors.BG)
        renderer.render_map(world)
        renderer.render_creatures(world)
        renderer.blit_to_screen(0, 0)
        hud.render(world, paused, speed_mult)

        pygame.display.flip()
        clock.tick(FPS)

    # выход — автоматически сохраняем итог
    _save_report(world, "./output_app")
    pygame.quit()
    print("Итоговый отчёт сохранён в ./output_app/")


# -----------------------------------------------------------------------------
# Сохранение статистики и отчёта
# -----------------------------------------------------------------------------

def _save_report(world: World, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    pop = Counter(c.species_name for c in world.creatures)

    # JSON
    stats = {
        "seed": world.seed,
        "tick": world.tick,
        "final_population": dict(pop),
        "births": dict(world.births),
        "deaths": dict(world.deaths),
        "disasters": [
            {"tick": d.tick, "kind": d.kind, "message": d.message}
            for d in world.disasters
        ],
        "population_history": world.population_history,
        "gene_history": {k: v for k, v in world.gene_history.items()},
    }
    with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Markdown-отчёт
    survivors = [sp for sp, n in pop.items() if n > 0]
    extinct = [sp for sp in SPECIES if sp not in survivors]

    lines = []
    lines.append("# Отчёт о симуляции Aetheris (GUI)\n")
    lines.append(f"- Seed: **{world.seed}**\n")
    lines.append(f"- Тиков: **{world.tick}**\n")
    lines.append(f"- Всего существ в финале: **{len(world.creatures)}**\n")
    lines.append(f"- Видов выжило: **{len(survivors)} из {len(SPECIES)}**\n\n")

    lines.append("## Популяции\n\n")
    lines.append("| Вид | Старт | Финал | Δ |\n")
    lines.append("|-----|------:|------:|--:|\n")
    for sp_name, sp in SPECIES.items():
        end = pop.get(sp_name, 0)
        lines.append(f"| {sp_name} | {sp.start_pop} | {end} | {end - sp.start_pop:+d} |\n")

    lines.append("\n## Какие виды выжили\n\n")
    if survivors:
        for s in survivors:
            lines.append(f"- **{s}** — {pop[s]} особей\n")
    else:
        lines.append("- (никого)\n")

    lines.append("\n## Какие виды вымерли\n\n")
    if extinct:
        for s in extinct:
            lines.append(f"- **{s}**\n")
    else:
        lines.append("- (никто)\n")

    lines.append("\n## Почему\n\n")
    lines.append(_explain_outcomes(world, pop, survivors, extinct))

    lines.append("\n## Эволюция (средние гены, последние значения)\n\n")
    lines.append("| Вид | speed | vision | aggression | intellect | stamina |\n")
    lines.append("|-----|------|------|------|------|------|\n")
    for sp_name, sp in SPECIES.items():
        hist = world.gene_history.get(sp_name, [])
        last_nonempty = next((h for h in reversed(hist) if h), {})
        if not last_nonempty:
            row = [sp_name, "—", "—", "—", "—", "—"]
        else:
            row = [
                sp_name,
                f"{sp.speed}→{last_nonempty.get('speed',0):.2f}",
                f"{sp.vision}→{last_nonempty.get('vision',0):.2f}",
                f"{sp.aggression}→{last_nonempty.get('aggression',0):.2f}",
                f"{sp.intellect}→{last_nonempty.get('intellect',0):.2f}",
                f"{sp.stamina}→{last_nonempty.get('stamina',0):.2f}",
            ]
        lines.append("| " + " | ".join(row) + " |\n")

    if world.disasters:
        lines.append("\n## Катастрофы\n\n")
        for d in world.disasters:
            lines.append(f"- t={d.tick}: {d.message}\n")

    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.writelines(lines)


def _explain_outcomes(world, pop, survivors, extinct) -> str:
    """Грубая эвристика для текстового объяснения."""
    parts = []
    if not survivors:
        parts.append("Все виды вымерли — экосистема не справилась с давлением.\n")
        return "".join(parts)

    top = pop.most_common(1)[0][0] if pop else None
    if top:
        from app.world.tiles import TERRAIN_PROPS
        sp = SPECIES[top]
        biomes = ", ".join(TERRAIN_PROPS[t].name for t in sp.preferred)
        parts.append(f"- Доминирует **{top}** ({sp.description.lower()}). "
                     f"Базовая stamina={sp.stamina}, ниша: {biomes}.\n")

    for ex in extinct:
        sp = SPECIES[ex]
        reasons = []
        if sp.diet == "carnivore":
            reasons.append("исчезла добыча после первых вымираний")
        if len(sp.forbidden) >= 5:
            reasons.append("очень узкая ниша по биомам")
        if sp.stamina <= 5:
            reasons.append("низкая выносливость в климатических катастрофах")
        if sp.start_pop < 30:
            reasons.append("малая стартовая популяция → демографический риск")
        if not reasons:
            reasons.append("проиграл конкуренцию за ресурсы")
        parts.append(f"- **{ex}** вымер: " + "; ".join(reasons) + ".\n")

    # тренд экосистемы
    if len(world.population_history) >= 2:
        first = sum(world.population_history[0].values())
        last = sum(world.population_history[-1].values())
        if last > first * 1.2:
            parts.append("\nЭкосистема **расширилась** относительно старта — освободившиеся ниши заняли универсалы.\n")
        elif last < first * 0.6:
            parts.append("\nЭкосистема **схлопывается** — несколько каскадов вымираний и катастроф.\n")
        else:
            parts.append("\nЭкосистема **в относительном равновесии**.\n")
    return "".join(parts)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Aetheris desktop simulation")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT,
                        help="зерно генератора (по умолчанию 42)")
    parser.add_argument("--tps", type=float, default=float(TICKS_PER_SECOND),
                        help="базовых тиков в секунду (по умолчанию 6)")
    parser.add_argument("--headless", action="store_true",
                        help="без GUI — только прогнать симуляцию")
    parser.add_argument("--ticks", type=int, default=300,
                        help="(headless) сколько тиков симулировать")
    parser.add_argument("--out", type=str, default="./output_app",
                        help="(headless) папка для отчёта")
    args = parser.parse_args()

    if args.headless:
        run_headless(args.seed, args.ticks, args.out)
    else:
        run_gui(args.seed, args.tps)


if __name__ == "__main__":
    main()
