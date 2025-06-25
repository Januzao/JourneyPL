# door_notifier.py
import pygame
from pathlib import Path
from resource_manager import ResourceManager
from settings import *


class DoorNotifier:
    """Показывает баннер двери на экране."""
    DISPLAY_TIME = 4000  # общее время показа (мс)
    FADE_DELAY = 500  # время до начала затухания (мс)
    FADE_TIME = DISPLAY_TIME - FADE_DELAY  # длительность затухания

    def __init__(self, display_surface):
        self.display_surface = None
        self.display = display_surface
        self.active = False
        self.start_time = 0
        self.image = None
        self.rect = None
        w, h = pygame.display.get_surface().get_size()

    def _reposition(self) -> None:
        """Помещает баннер внизу по центру, отталкиваясь от окна."""
        if not self.image:
            return
        w, h = self.display_surface.get_size()
        self.rect = self.image.get_rect(midbottom=(w // 2, int(h * 0.95)))

    def show(self) -> None:
        """Запускает показ баннера двери."""
        banner_path: Path = UI_DIR / "door_banner.png"
        img = ResourceManager.load_image(banner_path)

        self.image = img.convert_alpha()
        self.image.set_alpha(255)  # стартовая непрозрачность

        # Каждое новое появление — актуализируем ссылку на окно и позицию.
        self.display_surface = pygame.display.get_surface()
        self._reposition()

        self.start_time = pygame.time.get_ticks()
        self.active = True

    def update(self):
        """Управление временем показа и плавным затуханием."""
        if not self.active:
            return
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.DISPLAY_TIME:
            # Баннер полностью скрывается по истечении времени
            self.active = False
        elif elapsed > self.FADE_DELAY:
            # Начинаем затухание
            fade_elapsed = elapsed - self.FADE_DELAY
            alpha = int(255 * (1 - fade_elapsed / self.FADE_TIME))
            self.image.set_alpha(max(alpha, 0))

    def draw(self):
        """Отрисовать баннер, если он активен."""
        if self.active and self.image:
            self.display.blit(self.image, self.rect)
