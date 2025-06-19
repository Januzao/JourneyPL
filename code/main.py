import pygame
from pygame.math import Vector2
from pathlib import Path
from collections import deque

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE, MAPS_DIR
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from inventory import Inventory
from item_manager import ItemManager
from music_manager import MusicManager

class Game:
    def __init__(self):
        # Ініціалізація Pygame та аудіо
        pygame.init()
        pygame.mixer.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # Фонова музика
        self.music = MusicManager(volume=0.3)
        self.music.load('A_Walk_Along_the_Gates.mp3')
        self.music.play(loops=-1)

        # Інвентар
        self.inventory = Inventory()

        # Групи спрайтів
        self.all_sprites       = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites      = pygame.sprite.Group()

        # Завантаження карти
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'map.tmx')

        # Налаштування світу, гравця та reachable-зони
        self.setup()

        # Менеджер предметів
        self.item_manager = ItemManager(
            self.tmx,
            self.all_sprites,
            self.item_sprites,
            self.inventory,
            self.player,
            self.collision_sprites,
            self.reachable
        )
        self.item_manager.spawn_items()

    def setup(self):
        # Очищення попередніх спрайтів
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_sprites.empty()

        # Малюємо землю
        for x, y, img in self.tmx.get_layer_by_name('Ground').tiles():
            WorldSprite((x*TILE_SIZE, y*TILE_SIZE), img, [self.all_sprites], ground=True)
        for x, y, img in self.tmx.get_layer_by_name('Ground_items').tiles():
            WorldSprite((x*TILE_SIZE, y*TILE_SIZE), img, [self.all_sprites], ground=True)

        # Видимі об’єкти
        for obj in self.tmx.get_layer_by_name('Objects'):
            WorldSprite(
                (obj.x, obj.y),
                f'data/graphics/objects/{obj.name}.png',
                [self.all_sprites, self.collision_sprites]
            )

        # Колізії
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0,0,0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # Створюємо гравця
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    Vector2(obj.x, obj.y),
                    [self.all_sprites],
                    self.collision_sprites
                )
                self.all_sprites.set_target(self.player)
                break

        # BFS для reachable-тайлів
        free = set()
        w, h = self.tmx.width, self.tmx.height
        for tx in range(w):
            for ty in range(h):
                cell = pygame.Rect(tx*TILE_SIZE, ty*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not any(col.rect.colliderect(cell) for col in self.collision_sprites):
                    free.add((tx, ty))

        start = (
            self.player.rect.centerx // TILE_SIZE,
            self.player.rect.centery  // TILE_SIZE
        )
        reachable = {start}
        queue = deque([start])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (cx+dx, cy+dy)
                if nb in free and nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)

        self.reachable = reachable

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_i:
                    self.inventory.toggle()
                elif e.key == pygame.K_r:
                    self.setup()
                    # після reset треба знову спавнити предмети
                    self.item_manager = ItemManager(
                        self.tmx,
                        self.all_sprites,
                        self.item_sprites,
                        self.inventory,
                        self.player,
                        self.collision_sprites,
                        self.reachable
                    )
                    self.item_manager.spawn_items()

    def update(self, dt):
        self.item_manager.check_pickups()
        self.all_sprites.update(dt)

    def render(self):
        self.display.fill('black')
        self.all_sprites.draw()
        self.inventory.render(self.display)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 600
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

if __name__ == '__main__':
    Game().run()
