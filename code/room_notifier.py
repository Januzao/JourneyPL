import pygame
from pathlib import Path
from resource_manager import ResourceManager
from settings import *


class RoomNotifier:
    """Показывает баннер с названием комнаты на 5 секунд."""
    DISPLAY_TIME = 5000    # общее время показа (мс)
    FADE_DELAY  = 2000    # время до старта фейда (мс)
    FADE_TIME   = DISPLAY_TIME - FADE_DELAY  # длительность фейда

    def __init__(self, display_surface):
        self.display = display_surface
        self.active = False
        self.start_time = 0
        self.image = None
        self.rect = None

    def show(self, room_name: str):
        """Запустить показ баннера для комнаты room_name."""
        banner_path = UI_DIR / f"{room_name}_banner.png"
        # загружаем с альфа-каналом
        img = ResourceManager.load_image(banner_path)
        self.image = img.convert_alpha()
        # сразу полная непрозрачность
        self.image.set_alpha(255)
        # позиционируем
        self.rect = self.image.get_rect(midtop=(WINDOW_WIDTH // 2, 20))
        self.start_time = pygame.time.get_ticks()
        self.active = True

    def update(self):
        """Уменьшаем альфу по истечении времени, и выключаем."""
        if not self.active:
            return

        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.DISPLAY_TIME:
            # Полностью скрываем баннер по истечении общего времени
            self.active = False
        elif elapsed > self.FADE_DELAY:
            # Начинаем фейд
            fade_elapsed = elapsed - self.FADE_DELAY
            # alpha от 255 → 0 за FADE_TIME
            alpha = int(255 * (1 - fade_elapsed / self.FADE_TIME))
            self.image.set_alpha(max(alpha, 0))

    def draw(self):
        """Нарисовать баннер, если он активен."""
        if self.active and self.image:
            self.display.blit(self.image, self.rect)
