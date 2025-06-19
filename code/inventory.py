import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, UI_DIR, PARENT_DIR
from resource_manager import ResourceManager

class Inventory:
    def __init__(self):
        self.is_open = False

        audio_path = PARENT_DIR / 'data' / 'audio' / 'book-opening.mp3'
        self.sound = pygame.mixer.Sound(str(audio_path))

        try:
            self.bg = ResourceManager.load_image(UI_DIR / 'inventory_book.png')
            # масштабуємо зображення під нові розміри
            self.bg = pygame.transform.scale(self.bg, (600, 500))
        except Exception:
            self.bg.fill((50, 50, 50))

        self.bg_rect = self.bg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

    def toggle(self):
        self.is_open = not self.is_open
        self.sound.play()

    def render(self, display: pygame.Surface):
        if self.is_open:
            display.blit(self.bg, self.bg_rect)
