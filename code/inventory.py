import pygame
import pygame.surfarray as surfarray
import numpy as np
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, UI_DIR, PARENT_DIR
from resource_manager import ResourceManager

class Inventory:
    def __init__(self):
        self.is_open = False
        audio_path = PARENT_DIR / 'data' / 'audio' / 'inventory_open.mp3'
        self.sound = pygame.mixer.Sound(str(audio_path))
        try:
            self.bg = ResourceManager.load_image(UI_DIR / 'inventory_book.png')
            # масштабуємо зображення під нові розміри
            self.bg = pygame.transform.scale(self.bg, (600, 500))
        except Exception:
            self.bg = pygame.Surface((600, 400))
            self.bg.fill((50, 50, 50))
        self.bg_rect = self.bg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.items: dict[str, dict] = {}

    def toggle(self):
        self.is_open = not self.is_open
        self.sound.play()

    def register_item(self, item_id: str, image: pygame.Surface):
        if item_id in self.items:
            return
        gray = self._grayscale_surface(image)
        self.items[item_id] = {'orig': image, 'gray': gray, 'picked': False}

    def pickup_item(self, item_id: str):
        if item_id in self.items:
            self.items[item_id]['picked'] = True

    def _grayscale_surface(self, surface: pygame.Surface) -> pygame.Surface:
        arr = surfarray.array3d(surface)
        lum = (arr[:, :, 0] * 0.3 + arr[:, :, 1] * 0.59 + arr[:, :, 2] * 0.11).astype(np.uint8)
        gray_arr = np.stack((lum,)*3, axis=2)
        gray_surf = surfarray.make_surface(gray_arr)
        return gray_surf.convert_alpha()

    def render(self, display: pygame.Surface):
        if not self.is_open:
            return
        display.blit(self.bg, self.bg_rect)
        x0 = self.bg_rect.left + 20
        y0 = self.bg_rect.top + 20
        slot = 64
        pad = 10
        for idx, (item_id, data) in enumerate(self.items.items()):
            img = data['orig'] if data['picked'] else data['gray']
            icon = pygame.transform.scale(img, (slot, slot))
            x = x0 + (idx % 5) * (slot + pad)
            y = y0 + (idx // 5) * (slot + pad)
            display.blit(icon, (x, y))