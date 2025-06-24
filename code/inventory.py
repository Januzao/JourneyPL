import pygame
import pygame.surfarray as surfarray
import numpy as np
from settings import TILE_SIZE, UI_DIR, PARENT_DIR
from resource_manager import ResourceManager
import re  # regex for ID normalization


class Inventory:
    def __init__(self):
        self.is_open = False
        audio_path = PARENT_DIR / 'data' / 'audio' / 'sounds' / 'inventory_open.mp3'
        try:
            self.sound = pygame.mixer.Sound(str(audio_path))
        except:
            self.sound = None

        # Load and scale background
        try:
            bg = ResourceManager.load_image(UI_DIR / 'inventory_book.png')
            self.bg = pygame.transform.scale(bg, (600, 500))
        except:
            self.bg = pygame.Surface((600, 500))
            self.bg.fill((50, 50, 50))

        # items storage: id → {'orig': Surface, 'gray': Surface, 'picked': bool}
        self.items = {}

    def toggle(self):
        """Open/close inventory and play sound."""
        self.is_open = not self.is_open
        if self.sound:
            self.sound.play()

    @staticmethod
    def normalize_item_id(item_id: str) -> str:
        return re.sub(r'_[0-9]+x[0-9]+$', '', item_id)

    def register_item(self, item_id: str, image: pygame.Surface):
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            return
        gray = self._grayscale_surface(image)
        self.items[base_id] = {'orig': image, 'gray': gray, 'picked': False}

    def pickup_item(self, item_id: str):
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            self.items[base_id]['picked'] = True

    def _grayscale_surface(self, surface: pygame.Surface) -> pygame.Surface:
        arr = surfarray.array3d(surface)
        lum = (arr[:, :, 0] * 0.3 + arr[:, :, 1] * 0.59 + arr[:, :, 2] * 0.11).astype(np.uint8)
        gray_arr = np.stack((lum,) * 3, axis=2)
        gray_surf = surfarray.make_surface(gray_arr)
        return gray_surf.convert_alpha()

    def render(self, display: pygame.Surface):
        """Draw inventory centered on screen regardless of resolution."""
        if not self.is_open:
            return

        # Recompute background rect centered on current display size
        disp_rect = display.get_rect()
        bg_rect = self.bg.get_rect(center=disp_rect.center)

        # Draw background
        display.blit(self.bg, bg_rect)

        # Icon parameters
        icon_size = int(TILE_SIZE * 1.5)
        vertical_spacing = icon_size + 30

        # Positions relative to bg_rect
        left_x = bg_rect.left + 100
        left_y = bg_rect.top + 80
        right_x = bg_rect.left + bg_rect.width - icon_size - 100
        right_y = bg_rect.top + 120

        # Draw up to 10 items in two columns
        for idx, (item_id, data) in enumerate(self.items.items()):
            if idx >= 10:
                break

            base_img = data['orig'] if data['picked'] else data['gray']
            icon = pygame.transform.scale(base_img, (icon_size, icon_size))

            # Rotate and position left/right
            if idx % 2 == 0:
                icon = pygame.transform.rotate(icon, 45)
                x = left_x
                y = left_y + (idx // 2) * vertical_spacing
            else:
                icon = pygame.transform.rotate(icon, -45)
                x = right_x
                y = right_y + (idx // 2) * vertical_spacing

            display.blit(icon, (x, y))
