# Aetheris — генеративная симуляция мира с эволюцией существ

Самодостаточная Python-симуляция мира 50×50 с 8 видами существ,
5-параметровой эволюцией, дискретным временем и природными катастрофами.

**Никаких внешних зависимостей** — только стандартная библиотека Python ≥ 3.8.

## Быстрый запуск

```bash
python3 simulation.py
```

С параметрами:

```bash
python3 simulation.py --ticks 300 --seed 42 --out ./output
```

| Флаг | По умолчанию | Назначение |
|---|---|---|
| `--ticks` | 300 | Сколько тиков симулировать |
| `--seed` | 42 | Зерно ГПСЧ (одинаковый seed → одинаковый мир) |
| `--out` | `./output` | Папка для выходных файлов |
| `--quiet` | off | Не печатать прогресс в консоль |

## Что генерируется

После запуска в `--out` появятся:

| Файл | Что в нём |
|---|---|
| `world_map_initial.txt` | ASCII-карта мира на старте + размещение существ |
| `world_map_final.txt` | ASCII-карта мира в финале |
| `food_heatmap.txt` | Heatmap биомассы (` .:-=+*#%@`) |
| `population_chart.txt` | ASCII-графики популяций по видам |
| `stats.json` | Полная статистика: история популяции, генов, смертей, событий |
| `report.md` | Автоматический отчёт об итогах симуляции |

## Документация

| Файл | О чём |
|---|---|
| [`docs/world.md`](docs/world.md) | Концепция вселенной: климат, ландшафты, ресурсы, катастрофы |
| [`docs/species.md`](docs/species.md) | 8 видов существ: параметры, поведение, экология |
| [`docs/evolution.md`](docs/evolution.md) | Правила эволюции: гены, мутации, отбор, размножение |
| [`docs/report.md`](docs/report.md) | Подробный разбор референсного прогона `seed=42, ticks=250` |

## Пример вывода

```
=== Запуск симуляции на 250 тиков ===
t=  20  всего= 366  Grazor=  2  Lupax= 64  Terrax=  4  Skywing=181  Shakrit= 34  Mycor=  4  Aquor= 69  Cryon=  8
t=  60  всего=1049  Grazor=  0  Lupax= 16  Terrax=  4  Skywing=977  Shakrit= 37  Mycor=  0  Aquor=  2  Cryon= 13
t= 120  всего= 183  Grazor=  0  Lupax=  0  Terrax=  3  Skywing=135  Shakrit= 26  Mycor=  0  Aquor=  0  Cryon= 19
t= 240  всего= 227  Grazor=  0  Lupax=  0  Terrax=  2  Skywing=  1  Shakrit=101  Mycor=  0  Aquor=  0  Cryon=123
=== Симуляция завершена ===
```

Каскад: травоядные → плотоядные → падальщики → доминирование универсалов.
Подробный разбор — в `docs/report.md`.

## Структура репозитория

```
.
├── README.md
├── simulation.py            ← основной код, ~700 строк, stdlib only
├── docs/
│   ├── world.md
│   ├── species.md
│   ├── evolution.md
│   └── report.md            ← интерпретация результатов
└── output/                  ← пример прогона seed=42, ticks=250
    ├── world_map_initial.txt
    ├── world_map_final.txt
    ├── food_heatmap.txt
    ├── population_chart.txt
    ├── stats.json
    └── report.md            ← автоматический машинный отчёт
```

## Легенда карты

```
~ вода       # лес        ^ горы      . пустыня
, равнина    * тундра     $ ресурсы

G Grazor     L Lupax      T Terrax    S Skywing
K Shakrit    M Mycor      A Aquor     C Cryon
```
