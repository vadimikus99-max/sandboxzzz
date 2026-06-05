# src/main.py
import os
import numpy as np
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from src.simulation import simulation_step
from src.renderer import SandRenderer
from src.input import InputHandler
from src.elements import PROPS

# Размер сетки (подбери под телефон: 300x200 = 60k клеток, нормально для Numba)
GRID_W, GRID_H = 300, 200 
CELL_SIZE = 3 # Пикселей на клетку (рендерим в текстуру 300x200, потом растягиваем на экран)

class SandboxWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.w, self.h = GRID_W, GRID_H
        
        # Состояние симуляции
        self.grid = np.zeros((self.h, self.w), dtype=np.uint8)
        self.temp_grid = np.full((self.h, self.w), 20.0, dtype=np.float32) # 20°C
        
        # Рендерер
        self.renderer = SandRenderer(self.w, self.h, CELL_SIZE)
        
        # Графика Kivy: Один Rectangle с текстурой
        with self.canvas:
            Color(1, 1, 1, 1) # Белый, чтоб не тенить текстуру
            self.rect = Rectangle(texture=self.renderer.get_texture(), pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Инпут
        self.input = InputHandler(self)
        
        # Запуск лупа (60 FPS target)
        Clock.schedule_interval(self.update, 1/60.0)
        
        # Тестовый спавн
        self.spawn_test_scene()

    def spawn_test_scene):
        # Половина песка, половина воды, лава внизу
        self.grid[self.h//2:, :] = 1 # Sand
        self.grid[:self.h//2, :self.w//2] = 2 # Water
        self.grid[self.h-5:, self.w//2:] = 7 # Lava
        self.temp_grid[self.h-5:, self.w//2:] = 1200.0

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def get_widget_pos(self, tx, ty):
        """Конвертация Touch -> Grid Coords с учетом Aspect Ratio"""
        # Виджет может быть не на весь экран, или иметь другой aspect ratio
        # Простая версия: растягиваем текстуру на весь виджет
        if not self.collide_point(tx, ty): return None, None
        # Относительные координаты 0..1
        rx = (tx - self.x) / self.width
        ry = (ty - self.y) / self.height
        # В координаты сетки
        gx = int(rx * self.w)
        gy = int((1.0 - ry) * self.h) # Y инвертирован в Kivy (снизу вверх)
        return gx, gy

    def set_cell(self, x, y, mat_id):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y, x] = mat_id
            # Сброс температуры при спавне
            if mat_id != 0:
                self.temp_grid[y, x] = PROPS[mat_id, 3]

    def update(self, dt):
        # 1. Физика (Numba параллельно)
        # Копии не нужны, simulation_step меняет in-place
        simulation_step(self.grid, self.temp_grid, self.w, self.h, dt)
        
        # 2. Рендер (NumPy -> Texture)
        self.renderer.update_texture(self.grid, self.temp_grid)
        # Текстура обновилась в GPU, Rectangle обновится сам на следующем кадре

class SandboxApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.12, 1)
        return SandboxWidget()

if __name__ == '__main__':
    SandboxApp().run()
