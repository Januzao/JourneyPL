# groups.py
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        # Основна поверхня для відмалювання
        self.display_surface = pygame.display.get_surface()
        # Вектор зсуву камери
        self.offset = pygame.math.Vector2()
        # Піврозміри екрана для обчислень центру
        self.half_w = WINDOW_WIDTH // 2
        self.half_h = WINDOW_HEIGHT // 2
        # Ціль камери (наприклад, гравець)
        self.target = None
        # Список шарів для паралаксу: [(surface, speed), ...]
        self.parallax_layers = []

    def set_target(self, sprite: pygame.sprite.Sprite) -> None:
        """Встановлює, за чим слідкуватиме камера."""
        self.target = sprite

    def add_parallax_layer(self, surface: pygame.Surface, speed: float) -> None:
        """Додає фон з власною швидкістю зсуву для паралаксу."""
        self.parallax_layers.append((surface, speed))

    def _calculate_offset(self) -> None:
        """Оновлює self.offset на основі позиції target."""
        if not self.target:
            return
        self.offset.x = -(self.target.rect.centerx - self.half_w)
        self.offset.y = -(self.target.rect.centery - self.half_h)

    def draw(self) -> None:
        """Малює паралакс, землю та об'єкти, відсортовані за центром по Y."""
        # Оновлюємо зсув камери
        self._calculate_offset()

        # Малюємо паралакс-шари
        for bg_surface, speed in self.parallax_layers:
            parallax_offset = self.offset * speed
            self.display_surface.blit(bg_surface, parallax_offset)

        # Розділяємо спрайти на землю і об'єкти
        ground_sprites = [s for s in self if getattr(s, 'ground', False)]
        object_sprites = [s for s in self if not getattr(s, 'ground', False)]

        # Намалювати земляні спрайти, потім об'єкти з сортуванням по Y
        for layer in (ground_sprites, object_sprites):
            for sprite in sorted(layer, key=lambda s: s.rect.centery):
                self.display_surface.blit(
                    sprite.image,
                    sprite.rect.topleft + self.offset
                )