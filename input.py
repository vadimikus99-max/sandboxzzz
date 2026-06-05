# src/input.py
from kivy.core.window import Window
from kivy.vector import Vector
from src.elements import (SAND, WATER, STONE, FIRE, WOOD, LAVA, ACID, EMPTY)

BRUSHES = [SAND, WATER, STONE, FIRE, WOOD, LAVA, ACID, EMPTY]
BRUSH_NAMES = ["ПЕСОК", "ВОДА", "КАМЕНЬ", "ОГОНЬ", "ДЕРЕВО", "ЛАВА", "КИСЛОТА", "СТЕРКА"]
BRUSH_RADIUS = 3

class InputHandler:
    def __init__(self, sim_engine):
        self.sim = sim_engine
        self.current_brush_idx = 0
        self.brush_radius = BRUSH_RADIUS
        Window.bind(on_touch_down=self.on_touch, on_touch_move=self.on_touch)
        # Кнопки клавиатуры (для ПК теста) / можно повесить на UI кнопки
        Window.bind(on_key_down=self.on_key)
        
    def on_key(self, instance, key, scancode, codepoint, modifiers):
        if '1' <= codepoint <= '8':
            self.current_brush_idx = int(codepoint) - 1
            print(f"Brush: {BRUSH_NAMES[self.current_brush_idx]}")
        elif codepoint == '+' or codepoint == '=':
            self.brush_radius = min(20, self.brush_radius + 1)
        elif codepoint == '-':
            self.brush_radius = max(1, self.brush_radius - 1)
            
    def on_touch(self, instance, touch):
        if touch.is_mouse_scrolling: return False
        # Конвертация экранных координат в координаты сетки
        # Нужно знать offset виджета. Передадим через sim_engine.pos_widget
        wx, wy = self.sim.get_widget_pos(touch.x, touch.y)
        if wx is None: return
        
        self.paint(wx, wy)
        return True
        
    def paint(self, cx, cy):
        mat_id = BRUSHES[self.current_brush_idx]
        r = self.brush_radius
        w, h = self.sim.w, self.sim.h
        
        # Круговая кисть (оптимизация: квадрат + проверка dist^2)
        r2 = r * r
        for dy in range(-r, r+1):
            y = cy + dy
            if y < 0 or y >= h: continue
            for dx in range(-r, r+1):
                x = cx + dx
                if x < 0 or x >= w: continue
                if dx*dx + dy*dy <= r2:
                    # Шанс не закрашивать всю область (эффект распыления)
                    if mat_id != EMPTY and __import__('random').random() < 0.8: continue
                    self.sim.set_cell(x, y, mat_id)
