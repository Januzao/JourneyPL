# inventory.py

import math
import pygame
import pygame.surfarray as surfarray
import numpy as np
import re
from settings import *
from resource_manager import ResourceManager


class InventoryItem:
    """Element of the inventory: holds color/gray image and picked state."""

    def __init__(self, item_id: str, image: pygame.Surface):
        base_id = Inventory.normalize_item_id(item_id)
        self.id = base_id
        self.orig_image = image
        self.gray_image = self._create_gray(image)
        self.picked = False

    @staticmethod
    def _create_gray(image: pygame.Surface) -> pygame.Surface:
        """Create a grayscale copy of the image."""
        arr = surfarray.array3d(image)
        lum = (
            arr[:, :, 0] * 0.3 +
            arr[:, :, 1] * 0.59 +
            arr[:, :, 2] * 0.11
        ).astype(np.uint8)
        gray_arr = np.stack((lum,) * 3, axis=2)
        gray_surf = surfarray.make_surface(gray_arr)
        return gray_surf.convert_alpha()

    def get_display_image(self) -> pygame.Surface:
        """Return colored image if picked, otherwise gray."""
        return self.orig_image if self.picked else self.gray_image


class Inventory:
    """Inventory: stores InventoryItems, handles pagination and rendering."""

    ITEMS_PER_PAGE = 8
    ROTATION_ANGLE = 45
    ARROW_SIZE = 32

    def __init__(self):
        # Load and scale background
        self.bg = ResourceManager.load_image(UI_DIR / 'inventory_book.png')
        self.bg = pygame.transform.scale(self.bg, (600, 500))
        self.bg_rect = self.bg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        # State
        self.is_open = False
        self.items: dict[str, InventoryItem] = {}
        self.items_order: list[str] = []
        self.current_page = 0

        # Open/close sound
        audio_path = AUDIO_DIR / 'sounds' / 'inventory_open.mp3'
        self.sound = pygame.mixer.Sound(str(audio_path))

        # Arrow buttons
        self.btn_prev = ResourceManager.load_image(UI_DIR / 'arrow_book_left.png').convert_alpha()
        self.btn_next = ResourceManager.load_image(UI_DIR / 'arrow_book_right.png').convert_alpha()
        self.btn_prev = pygame.transform.scale(self.btn_prev, (self.ARROW_SIZE, self.ARROW_SIZE))
        self.btn_next = pygame.transform.scale(self.btn_next, (self.ARROW_SIZE, self.ARROW_SIZE))

        # Position arrows at book corners
        margin = 20
        self.btn_prev_rect = self.btn_prev.get_rect(
            bottomleft=(self.bg_rect.left + margin, self.bg_rect.bottom - margin)
        )
        self.btn_next_rect = self.btn_next.get_rect(
            bottomright=(self.bg_rect.right - margin, self.bg_rect.bottom - margin)
        )

        # Relative sticker positions (relative to top-left of bg_rect)
        self.sticker_offsets = [
            (60, 60),     # Slot 1
            (340, 60),    # Slot 2
            (160, 140),   # Slot 3
            (450, 130),   # Slot 4
            (60, 260),    # Slot 5
            (340, 260),   # Slot 6
            (150, 340),   # Slot 7
            (450, 340),   # Slot 8
        ]

        # Individual angles per sticker
        self.sticker_angles = [24, -12, -34, 22, -40, 35, 25, -35]

    def toggle(self):
        """Open or close the inventory, play sound."""
        self.is_open = not self.is_open
        self.sound.play()

    @staticmethod
    def normalize_item_id(item_id: str) -> str:
        """Strip size suffix (_WIDTHxHEIGHT) from item_id."""
        return re.sub(r'_\d+x\d+$', '', item_id)

    def register_item(self, item_id: str, image: pygame.Surface):
        """Add a new slot (gray by default) for this item_id."""
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            return
        item = InventoryItem(base_id, image)
        self.items[base_id] = item
        self.items_order.append(base_id)

    def pickup_item(self, item_id: str):
        """Mark an item as picked (colorful) when collected."""
        base_id = Inventory.normalize_item_id(item_id)
        if base_id in self.items:
            self.items[base_id].picked = True

    @property
    def num_pages(self) -> int:
        """Total number of pages needed."""
        return math.ceil(len(self.items_order) / Inventory.ITEMS_PER_PAGE)

    def next_page(self):
        """Go to next page, if any."""
        if self.current_page < self.num_pages - 1:
            self.current_page += 1

    def prev_page(self):
        """Go to previous page, if any."""
        if self.current_page > 0:
            self.current_page -= 1

    def handle_event(self, event: pygame.event.Event):
        """Respond to left-clicks on arrow buttons to flip pages."""
        if not self.is_open:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.num_pages > 1:
                if self.btn_prev_rect.collidepoint(event.pos):
                    self.prev_page()
                elif self.btn_next_rect.collidepoint(event.pos):
                    self.next_page()

    def render(self, display: pygame.Surface):
        """Draw the inventory UI (background, arrows, and items at fixed slots)."""
        if not self.is_open:
            return

        # Get display size (might have changed)
        win_width, win_height = display.get_size()

        # Recompute bg_rect to keep centered
        self.bg_rect = self.bg.get_rect(center=(win_width // 2, win_height // 2))

        # Update arrow rects
        margin = 20
        self.btn_prev_rect = self.btn_prev.get_rect(
            bottomleft=(self.bg_rect.left + margin, self.bg_rect.bottom - margin)
        )
        self.btn_next_rect = self.btn_next.get_rect(
            bottomright=(self.bg_rect.right - margin, self.bg_rect.bottom - margin)
        )

        # Draw background
        display.blit(self.bg, self.bg_rect)

        # Draw arrows if multiple pages
        if self.num_pages > 1:
            display.blit(self.btn_prev, self.btn_prev_rect)
            display.blit(self.btn_next, self.btn_next_rect)

        # Determine which items to show on this page
        icon_size = TILE_SIZE * 1.5
        start = self.current_page * Inventory.ITEMS_PER_PAGE
        page_ids = self.items_order[start: start + Inventory.ITEMS_PER_PAGE]

        for idx, item_id in enumerate(page_ids):
            if idx >= len(self.sticker_offsets):
                break

            orig = self.items[item_id].get_display_image()
            img = pygame.transform.scale(orig, (icon_size, icon_size))

            angle = self.sticker_angles[idx % len(self.sticker_angles)]
            rotated_img = pygame.transform.rotate(img, angle)

            offset_x, offset_y = self.sticker_offsets[idx]
            slot_center = (
                self.bg_rect.left + offset_x + icon_size // 2,
                self.bg_rect.top + offset_y + icon_size // 2,
            )
            rotated_rect = rotated_img.get_rect(center=slot_center)

            display.blit(rotated_img, rotated_rect.topleft)
