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
        # Background layers for parallax: list of (surface, speed)
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
        """
        Draw parallax layers and sprites, centering camera on target.
        Sprites with attribute ground=True are drawn before others.
        """
        # Refresh display surface in case of resize/fullscreen
        self.display_surface = pygame.display.get_surface()
        # Update camera offset
        self._calculate_offset()

        # Draw parallax background layers
        for bg_surface, speed in self.parallax_layers:
            parallax_offset = self.offset * speed
            self.display_surface.blit(bg_surface, parallax_offset)

        # Separate sprites by ground flag
        ground_sprites = [s for s in self if getattr(s, 'ground', False)]
        object_sprites = [s for s in self if not getattr(s, 'ground', False)]

        # Draw ground, then objects sorted by y-position for proper overlap
        for sprite_group in (ground_sprites, object_sprites):
            for sprite in sorted(sprite_group, key=lambda spr: spr.rect.centery):
                pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, pos)
