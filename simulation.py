# src/simulation.py
import numpy as np
from numba import njit, prange
from src.elements import (EMPTY, SAND, WATER, STONE, FIRE, SMOKE, WOOD, LAVA, STEAM, ACID, 
                          PROPS, REACTIONS)

@njit(fastmath=True, cache=True, nogil=True)
def swap(grid, temp_grid, x1, y1, x2, y2):
    """Быстрый обмен ячейками + температурой"""
    id1, id2 = grid[y1, x1], grid[y2, x2]
    t1, t2 = temp_grid[y1, x1], temp_grid[y2, x2]
    grid[y1, x1], grid[y2, x2] = id2, id1
    temp_grid[y1, x1], temp_grid[y2, x2] = t2, t1

@njit(fastmath=True, cache=True, nogil=True)
def try_move_down(grid, temp_grid, w, h, x, y, mat_id, density, state, viscosity):
    """Гравитация для жидкостей/пудообразных"""
    # Прямо вниз
    if y + 1 < h:
        if grid[y+1, x] == EMPTY or PROPS[grid[y+1, x], 0] < density:
            swap(grid, temp_grid, x, y, x, y+1)
            return True
    # Вбок (жидкости текут)
    if state == 1: # Liquid
        dirs = [-1, 1]
        # Рандомайзер направления без random модуля (через хэш координат)
        # seed = (x * 1664525 + y * 1013904223) & 0xFFFFFFFF
        # if seed & 1: dirs = [1, -1] 
        for dx in dirs:
            nx = x + dx
            if 0 <= nx < w:
                if grid[y, nx] == EMPTY or PROPS[grid[y, nx], 0] < density:
                    swap(grid, temp_grid, x, y, nx, y)
                    return True
                # Диагонали вниз
                if y + 1 < h:
                    if grid[y+1, nx] == EMPTY or PROPS[grid[y+1, nx], 0] < density:
                        swap(grid, temp_grid, x, y, nx, y+1)
                        return True
    return False

@njit(fastmath=True, cache=True, nogil=True)
def try_move_gas(grid, temp_grid, w, h, x, y, mat_id, density):
    """Газы летят вверх и разлетаются"""
    # Вверх
    if y - 1 >= 0:
        if grid[y-1, x] == EMPTY or PROPS[grid[y-1, x], 0] < density:
            swap(grid, temp_grid, x, y, x, y-1)
            return True
    # Вбок
    dirs = [-1, 1]
    for dx in dirs:
        nx = x + dx
        if 0 <= nx < w:
            if grid[y, nx] == EMPTY or PROPS[grid[y, nx], 0] < density:
                swap(grid, temp_grid, x, y, nx, y)
                return True
            if y - 1 >= 0:
                if grid[y-1, nx] == EMPTY or PROPS[grid[y-1, nx], 0] < density:
                    swap(grid, temp_grid, x, y, nx, y-1)
                    return True
    return False

@njit(fastmath=True, cache=True, nogil=True)
def process_heat(temp_grid, w, h, x, y, mat_id, conductivity, heat_cap, dt):
    """Теплопроводность (упрощенная явная схема)"""
    if conductivity <= 0: return
    my_temp = temp_grid[y, x]
    # 4 соседа
    for nx, ny in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
        if 0 <= nx < w and 0 <= ny < h:
            neigh_temp = temp_grid[ny, nx]
            diff = neigh_temp - my_temp
            # dT = k * dT * dt / (c * rho) ... упрощаем
            flux = conductivity * diff * dt * 0.25
            temp_grid[y, x] += flux / (heat_cap * 0.1 + 1e-5)
            temp_grid[ny, nx] -= flux / (heat_cap * 0.1 + 1e-5)

@njit(fastmath=True, cache=True, nogil=True)
def process_reactions(grid, temp_grid, w, h, x, y, mat_id):
    """Проверка реакций с соседями"""
    # Проверяем 4 соседа
    for nx, ny in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
        if 0 <= nx < w and 0 <= ny < h:
            neigh_id = grid[ny, nx]
            key = (mat_id, neigh_id)
            # Numba не любит dict в hot path, делаем if-else для ключевых реакций
            # Дерево горит
            if mat_id == WOOD and neigh_id == FIRE:
                if np.random.random() < 0.05: # Шанс загорания
                    grid[y, x] = FIRE
                    temp_grid[y, x] = 600.0
            # Вода гасит лаву -> камень + пар
            elif mat_id == WATER and neigh_id == LAVA:
                grid[y, x] = STEAM
                grid[ny, nx] = STONE
                temp_grid[y, x] = 110.0
                temp_grid[ny, nx] = 20.0
            # Кислота ест камень
            elif mat_id == ACID and neigh_id == STONE:
                grid[ny, nx] = EMPTY
            # Пар остывает -> вода
            elif mat_id == STEAM and temp_grid[y, x] < 100.0:
                grid[y, x] = WATER
                temp_grid[y, x] = 50.0
            # Огонь умирает без топлива
            elif mat_id == FIRE:
                if np.random.random() < 0.02:
                    grid[y, x] = SMOKE
                    temp_grid[y, x] = 100.0

@njit(parallel=True, fastmath=True, cache=True, nogil=True)
def simulation_step(grid, temp_grid, w, h, dt):
    """ГЛАВНЫЙ ЦИКЛ. Параллельный по Y (рядки независимы почти)."""
    # Порядок обновления важен: Газы -> Жидкости -> Твердые (песок) -> Статика
    # Делаем 2 прохода: вниз (песок/вода) и вверх (газ/пар)
    
    # Проход 1: Снизу вверх (Твердые/Жидкости падают)
    for y in range(h - 2, -1, -1): # h-2 чтоб y+1 был в границах
        for x in range(1, w - 1):
            mat_id = grid[y, x]
            if mat_id == EMPTY or mat_id == STONE: continue
            
            props = PROPS[mat_id]
            density = props[0]
            viscosity = props[1]
            state = int(props[6])
            
            # Температура
            process_heat(temp_grid, w, h, x, y, mat_id, props[5], props[4], dt)
            
            # Движение
            moved = False
            if state == 0: # Solid (Песок)
                # Песок падает и скользит
                if y + 1 < h:
                    below = grid[y+1, x]
                    if below == EMPTY or PROPS[below, 0] < density:
                        swap(grid, temp_grid, x, y, x, y+1)
                        moved = True
                    else:
                        # Скольжение
                        can_left = (x > 0 and (grid[y+1, x-1] == EMPTY or PROPS[grid[y+1, x-1], 0] < density))
                        can_right = (x < w-1 and (grid[y+1, x+1] == EMPTY or PROPS[grid[y+1, x+1], 0] < density))
                        if can_left and can_right:
                            if np.random.random() < 0.5: swap(grid, temp_grid, x, y, x-1, y+1)
                            else: swap(grid, temp_grid, x, y, x+1, y+1)
                            moved = True
                        elif can_left: swap(grid, temp_grid, x, y, x-1, y+1); moved = True
                        elif can_right: swap(grid, temp_grid, x, y, x+1, y+1); moved = True
            
            elif state == 1: # Liquid (Вода, Лава, Кислота)
                try_move_down(grid, temp_grid, w, h, x, y, mat_id, density, state, viscosity)
            
            # Реакции (после движения)
            process_reactions(grid, temp_grid, w, h, x, y, grid[y, x]) # grid[y,x] мог измениться

    # Проход 2: Сверху вниз (Газы поднимаются)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            mat_id = grid[y, x]
            if mat_id == EMPTY: continue
            props = PROPS[mat_id]
            state = int(props[6])
            density = props[0]
            
            if state == 2: # Gas (Огонь, Дым, Пар)
                try_move_gas(grid, temp_grid, w, h, x, y, mat_id, density)
                process_reactions(grid, temp_grid, w, h, x, y, grid[y, x])
            
            # Охлаждение огня/лавы со временем
            if mat_id == FIRE or mat_id == LAVA:
                temp_grid[y, x] *= 0.995
                if mat_id == FIRE and temp_grid[y, x] < 300:
                    grid[y, x] = SMOKE
