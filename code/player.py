import pygame
from settings import *
from os.path import join, dirname, abspath
from os import walk
from image_utils import *
from typing import Dict, List


class Player(pygame.sprite.Sprite):
    # Кеш кадрів анімації для всіх гравців
    _frames_cache: Dict[str, List[Surface]] = {}

    def __init__(
            self,
            pos: pygame.math.Vector2,
            groups: pygame.sprite.Group,
            collision_sprites: pygame.sprite.Group,
    ):
        super().__init__(groups)

        # Load sprites for player
        if not Player._frames_cache:
            for state in ['down', 'up', 'left', 'right']:
                paths = collect_image_paths(state)
                self.frames[state] = load_images_from_paths(paths)
        self.frames: Dict[str, List[Surface]] = Player._frames_cache

        self.state = 'down'
        self.frame_index = 0

        # default state
        self.image: Surface = self.frames[self.state][0]
        # collision rect
        self.rect: pygame.Rect = self.image.get_rect()
        # Smaller hitbox for player to avoid invisible collision problems
        self.hitbox_rect: pygame.Rect = self.rect.inflate(-60, -90)

        # movement
        self.direction: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        self.speed: float = 500
        self.collision_sprites = collision_sprites

    def handle_input(self) -> None:
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()
        else:
            # reset direction vector in-place до (0,0): оновлює x та y, не створюючи нового Vector2
            self.direction.update(0,0)

    def move(self, dt) -> None:
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    elif self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                else:  # vertical
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top
                    elif self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom

    def animate(self, dt):
        # set state of animation by movement
        if self.direction.x < 0:
            self.state = 'right'
        if self.direction.x > 0:
            self.state = 'left'
        if self.direction.y > 0:
            self.state = 'down'
        if self.direction.y > 0:
            self.state = 'up'

        # load frames
        frame_list = self.frames[self.state]

        if self.direction.length_squared() > 0:
            self.frame_index += ANIMATION_SPEED * dt
        else:
            self.frame_index = 0

        # cycle of animation
        frame = int(self.frame_index) % len(self.frames[self.state])
        self.image = frame_list[frame]

    def update(self, dt):
        self.handle_input()
        self.move(dt)
        self.animate(dt)
