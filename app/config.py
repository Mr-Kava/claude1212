"""Глобальные константы приложения."""

# --- Размер мира ---
MAP_W = 50
MAP_H = 50

# --- Окно ---
TILE_PX = 12                     # размер тайла в пикселях
MAP_PX_W = MAP_W * TILE_PX       # 600
MAP_PX_H = MAP_H * TILE_PX       # 600
SIDEBAR_PX = 340
WINDOW_W = MAP_PX_W + SIDEBAR_PX
WINDOW_H = MAP_PX_H
FPS = 30                         # частота кадров pygame

# --- Тикинг симуляции ---
TICKS_PER_SECOND = 6             # сколько обновлений мира в секунду (≠ FPS)
                                 # = 1 тик каждые FPS/TICKS_PER_SECOND кадров

# --- Параметры эволюции ---
MUTATION_RATE = 0.04             # 4% шанс крупной мутации на каждый ген
DISASTER_CHANCE = 0.012          # шанс катастрофы на тик
SEED_DEFAULT = 42
