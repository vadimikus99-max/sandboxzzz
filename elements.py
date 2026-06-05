# src/elements.py
from numba import njit, types
from numba.typed import Dict, List
import numpy as np

# --- ID Материалов ---
EMPTY = 0
SAND = 1
WATER = 2
STONE = 3
FIRE = 4
SMOKE = 5
WOOD = 6
LAVA = 7
STEAM = 8
ACID = 9

# --- Свойства (индексы массива props) ---
# 0: Density (плотность), 1: Viscosity (вязкость), 2: Flammability (горимость), 
# 3: Temp (температура), 4: Heat_Capacity, 5: Conductivity, 6: State (0=solid, 1=liquid, 2=gas), 7: Color_R, 8: Color_G, 9: Color_B, 10: Update_Priority

PROPS = np.array([
    # EMPTY
    [0.0, 0, 0, 20.0, 0, 0, 2, 0, 0, 0, 0],
    # SAND
    [1.5, 0, 0, 20.0, 800, 0.3, 0, 194, 178, 128, 1],
    # WATER
    [1.0, 4, 0, 20.0, 4184, 0.6, 1, 64, 164, 223, 2],
    # STONE
    [2.5, 0, 0, 20.0, 790, 2.0, 0, 100, 100, 100, 0],
    # FIRE (Газ)
    [0.3, 0, 0, 1500.0, 1000, 0.1, 2, 255, 100, 0, 3],
    # SMOKE (Газ)
    [0.5, 0, 0, 100.0, 1000, 0.1, 2, 80, 80, 80, 3],
    # WOOD
    [0.7, 0, 300, 20.0, 1700, 0.15, 0, 139, 69, 19, 0],
    # LAVA
    [3.0, 2, 0, 1200.0, 1000, 1.0, 1, 255, 50, 0, 1],
    # STEAM (Газ)
    [0.6, 0, 0, 110.0, 2000, 0.1, 2, 200, 200, 255, 3],
    # ACID
    [1.2, 3, 0, 20.0, 3000, 0.5, 1, 0, 255, 0, 2],
], dtype=np.float32)

# Цвета для рендера (отдельно, чтоб не таскать float32 в UI)
COLORS = {
    EMPTY: (0, 0, 0, 0),
    SAND: (194, 178, 128, 255),
    WATER: (64, 164, 223, 255),
    STONE: (100, 100, 100, 255),
    FIRE: (255, 100, 0, 255),
    SMOKE: (80, 80, 80, 200),
    WOOD: (139, 69, 19, 255),
    LAVA: (255, 50, 0, 255),
    STEAM: (200, 200, 255, 180),
    ACID: (0, 255, 0, 255),
}

# Реакции: (ID_А, ID_Б) -> (Результат_А, Результат_Б, Теплота)
# Упрощенно: дерево + огонь -> уголь/дым + тепло
REACTIONS = {
    (WOOD, FIRE): (SMOKE, FIRE, 500.0),
    (WATER, LAVA): (STONE, STEAM, 200.0),
    (ACID, STONE): (EMPTY, EMPTY, 0.0), # Кислота ест камень
}
