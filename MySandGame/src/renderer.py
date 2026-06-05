# src/renderer.py
import numpy as np
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from src.elements import COLORS, PROPS

class SandRenderer:
    def __init__(self, width, height, cell_size):
        self.w, self.h = width, height
        self.cell_size = cell_size
        # Текстура RGBA
        self.texture = Texture.create(size=(width, height), colorfmt='rgba')
        self.texture.mag_filter = 'nearest' # Пиксель-арт look
        self.buffer = np.zeros((height, width, 4), dtype=np.uint8)
        
    def update_texture(self, grid, temp_grid):
        """Векторизованный маппинг ID -> Color (NumPy быстрый)"""
        # Очистка
        # self.buffer[:] = 0 # Медленно. Лучше перезаписать только измененные? 
        # Но для простоты и 200x150 - перезапись всего буфера за 0.001с норма.
        
        # Векторизация: создаем массив цветов для всех ID сразу
        # Это хак: используем advanced indexing
        # grid shape (H, W) -> используем как индексы в LUT (Look Up Table)
        
        # Создаем LUT текстуру 256x1x4
        if not hasattr(self, 'color_lut'):
            lut = np.zeros((256, 4), dtype=np.uint8)
            for k, v in COLORS.items():
                if k < 256: lut[k] = v
            self.color_lut = lut
        
        # Магия NumPy: grid (H,W) -> buffer (H,W,4)
        # Нужно учесть температуру для огня/лавы (цвет зависит от T)
        base_colors = self.color_lut[grid] # (H, W, 4) - ОЧЕНЬ БЫСТРО
        
        # Температурный окрас для горячих веществ
        # Fire, Lava, Steam
        hot_mask = (grid == 4) | (grid == 7) | (grid == 8) # FIRE, LAVA, STEAM
        if np.any(hot_mask):
            # Нормализуем температуру 0..1 для хотов
            t = temp_grid[hot_mask]
            # Простой градиент: Cold(Red) -> Hot(White/Yellow)
            # R = 255, G = clamp(t/1000 * 255), B = 0
            r = 255
            g = np.clip((t / 1200.0) * 255, 0, 255).astype(np.uint8)
            b = 0
            a = base_colors[hot_mask, 3]
            base_colors[hot_mask] = np.stack([np.full_like(g, r), g, np.full_like(g, b), a], axis=1)
            
        self.buffer = base_colors
        # Загружаем в GPU
        self.texture.blit_buffer(self.buffer.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
        
    def get_texture(self):
        return self.texture
