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
        self.half_w = self.display_surface.get_width() // 2
        self.half_h = self.display_surface.get_height() // 2
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

    def draw(self, player):
        # Обновляем смещение камеры по позиции игрока
        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        # Собираем списки ground-спрайтов и остальных
        ground_sprites = []
        other_sprites = []
        for sprite in self.sprites():
            if getattr(sprite, "ground", False):
                ground_sprites.append(sprite)
            else:
                other_sprites.append(sprite)

        # Рисуем сначала «земные» спрайты без сортировки (фоновые)
        for sprite in ground_sprites:
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

        # Сортируем остальные спрайты по rect.bottom и рисуем
        for sprite in sorted(other_sprites, key=lambda s: s.rect.bottom):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

        # Если нужно, можно обновлять и self.lostsprites, но при простом выводе
        # достаточно вызывать blit, как показано выше.
