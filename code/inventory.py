# inventory.py

import pygame
import pygame.surfarray as surfarray
import numpy as np
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, UI_DIR, PARENT_DIR
from resource_manager import ResourceManager
import re  # Import regex module for ID normalization

class Inventory:
    def __init__(self):
        self.is_open = False
        audio_path = PARENT_DIR / 'data' / 'audio' / 'inventory_open.mp3'
        self.sound = pygame.mixer.Sound(str(audio_path))

        try:
            self.bg = ResourceManager.load_image(UI_DIR / 'inventory_book.png')
            self.bg = pygame.transform.scale(self.bg, (600, 500))
        except Exception:
            self.bg = pygame.Surface((600, 500))
            self.bg.fill((50, 50, 50))
        self.bg_rect = self.bg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        # id → {'orig': Surface, 'gray': Surface, 'picked': bool}
        self.items: dict[str, dict] = {}

    def toggle(self):
        """Відкрити/закрити інвентар з програванням звуку."""
        self.is_open = not self.is_open
        self.sound.play()

    @staticmethod
    def normalize_item_id(item_id: str) -> str:
        """Strip trailing size suffix (e.g. '_64x64') from an item ID."""
        return re.sub(r'_\d+x\d+$', '', item_id)

    def register_item(self, item_id: str, image: pygame.Surface):
        """Add an item icon to the inventory (initially gray, not picked)."""
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            return
        gray = self._grayscale_surface(image)
        self.items[base_id] = {'orig': image, 'gray': gray, 'picked': False}

    def pickup_item(self, item_id: str):
        """Mark an item as picked (show its colored icon)."""
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            self.items[base_id]['picked'] = True

    def _grayscale_surface(self, surface: pygame.Surface) -> pygame.Surface:
        """Повернути копію surface в градаціях сірого."""
        arr = surfarray.array3d(surface)
        lum = (arr[:, :, 0] * 0.3 +
               arr[:, :, 1] * 0.59 +
               arr[:, :, 2] * 0.11).astype(np.uint8)
        gray_arr = np.stack((lum,) * 3, axis=2)
        gray_surf = surfarray.make_surface(gray_arr)
        return gray_surf.convert_alpha()

    def render(self, display: pygame.Surface):
        """Намалювати вміст інвентаря, якщо він відкритий."""
        if not self.is_open:
            return

        # Фон книжки
        display.blit(self.bg, self.bg_rect)

        # Параметри іконок
        icon_size = int(TILE_SIZE * 1.5)  # 150% від TILE_SIZE
        vertical_spacing = icon_size + 30

        # Відступи для лівої та правої колонки
        left_x = self.bg_rect.left + 100
        left_y = self.bg_rect.top + 80
        right_x = self.bg_rect.left + self.bg_rect.width - icon_size - 100
        right_y = self.bg_rect.top + 120

        # Відобразити до 10 предметів: парно ліво/право
        for idx, (item_id, data) in enumerate(self.items.items()):
            if idx >= 10:
                break

            base_img = data['orig'] if data['picked'] else data['gray']
            icon = pygame.transform.scale(base_img, (icon_size, icon_size))

            if idx % 2 == 0:
                # парні: ліворуч, +45°
                icon = pygame.transform.rotate(icon, 45)
                x = left_x
                y = left_y + (idx // 2) * vertical_spacing
            else:
                # непарні: праворуч, -45°
                icon = pygame.transform.rotate(icon, -45)
                x = right_x
                y = right_y + (idx // 2) * vertical_spacing

            display.blit(icon, (x, y))
