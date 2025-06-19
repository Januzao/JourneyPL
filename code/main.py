import pygame
from pathlib import Path

from MusicManager import MusicManager
from pygame.examples.music_drop_fade import volume

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE,
    MAPS_DIR, UI_DIR, PARENT_DIR
)
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from collections import deque
from inventory import Inventory  # ← новий модуль


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.event.get()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        self.music = MusicManager(volume = 0.3)
        self.music.load('A_Walk_Along_the_Gates.mp3')
        self.music.play(loops =- 1)

        # Спрайт-групи
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

        # Завантажуємо карту TMX
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'map.tmx')

        # Інвентар з окремого файлу
        self.inventory = Inventory()

        # Підготовка світу
        self.setup()

    def setup(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_group.empty()

        # Малюємо ґрунт
        for x, y, img in self.tmx.get_layer_by_name('Ground').tiles():
            WorldSprite(
                (x * TILE_SIZE, y * TILE_SIZE),
                img,
                [self.all_sprites],
                ground=True
            )
        for x, y, img in self.tmx.get_layer_by_name('Ground_items').tiles():
            WorldSprite(
                (x * TILE_SIZE, y * TILE_SIZE),
                img,
                [self.all_sprites],
                ground=True
            )

        # Об’єкти і колізії
        for obj in self.tmx.get_layer_by_name('Objects'):
            WorldSprite(
                (obj.x, obj.y),
                f'data/graphics/objects/{obj.name}.png',
                [self.all_sprites, self.collision_sprites]
            )
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0, 0, 0))
            WorldSprite(
                (obj.x, obj.y),
                surf,
                [self.collision_sprites]
            )

        # Створюємо гравця (тільки в all_sprites)
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    pygame.math.Vector2(obj.x, obj.y),
                    [self.all_sprites],
                    self.collision_sprites
                )
                self.all_sprites.set_target(self.player)
                break


    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_i:
                    self.inventory.toggle()
                elif e.key == pygame.K_r:
                    self.setup()

    def update(self, dt):
        self.all_sprites.update(dt)

    def render(self):
        self.display.fill('black')
        self.all_sprites.draw()
        # Малюємо інвентар поверх всього
        self.inventory.render(self.display)
        pygame.display.update()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 600
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()


if __name__ == '__main__':
    Game().run()
