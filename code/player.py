# player.py
from typing import Dict, List
import pygame
from pygame import Surface
from settings import TILE_SIZE, ANIMATION_SPEED
from resource_manager import ResourceManager
from image_utils import collect_image_paths, load_images_from_paths

class Player(pygame.sprite.Sprite):
    _frames_cache: Dict[str, List[Surface]] = {}

    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        # Завантажуємо спрайти анімації один раз
        if not Player._frames_cache:
            for state in ('down', 'up', 'left', 'right'):
                paths = collect_image_paths(state)
                Player._frames_cache[state] = load_images_from_paths(paths)

        self.frames = Player._frames_cache
        self.state = 'down'
        self.frame_index = 0.0
        self.image = self.frames[self.state][0]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -90)

        self.direction = pygame.Vector2()
        self.speed = 200  # зменшили швидкість
        self.collisions = collision_sprites

    def handle_input(self):
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        # Виправлена інверсія
        dx = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        dy = int(keys[pygame.K_DOWN])  - int(keys[pygame.K_UP])
        self.direction.x = dx
        self.direction.y = dy
        if self.direction.length_squared():
            self.direction.normalize_ip()
        else:
            self.direction.update(0, 0)

    def apply_physics(self, dt: float) -> None:
        # Горизонталь
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        # Вертикаль
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        # Оновлюємо відображуваний прямокутник
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collisions:
            if sprite is self:
                continue  # пропускаємо самого себе
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x < 0:   # рух ліворуч
                        self.hitbox_rect.left = sprite.rect.right
                    elif self.direction.x > 0: # рух праворуч
                        self.hitbox_rect.right = sprite.rect.left
                else:  # вертикальна
                    if self.direction.y < 0:   # рух вгору
                        self.hitbox_rect.top = sprite.rect.bottom
                    elif self.direction.y > 0: # рух вниз
                        self.hitbox_rect.bottom = sprite.rect.top

    def update_animation(self, dt: float) -> None:
        if self.direction.x < 0:
            self.state = 'left'
        elif self.direction.x > 0:
            self.state = 'right'
        elif self.direction.y < 0:
            self.state = 'up'
        elif self.direction.y > 0:
            self.state = 'down'

        frames_list = self.frames[self.state]
        if self.direction.length_squared():
            self.frame_index += ANIMATION_SPEED * dt
        else:
            self.frame_index = 0

        idx = int(self.frame_index) % len(frames_list)
        self.image = frames_list[idx]

    def update(self, dt) -> None:
        self.handle_input()
        self.apply_physics(dt)
        self.update_animation(dt)
