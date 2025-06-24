# main.py

import pygame
from pygame.math import Vector2
from pathlib import Path
from collections import deque

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE, MAPS_DIR, STICKERS_DIR, PARENT_DIR
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from inventory import Inventory
from item_manager import ItemManager
from music_manager import MusicManager
from room_notifier import RoomNotifier
from menu import Menu

class Game:
    def __init__(self):
        # Ініціалізація Pygame та аудіо
        pygame.init()
        pygame.mixer.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # Room notifier
        self.room_notifier = RoomNotifier(self.display)
        initial_tmx = MAPS_DIR / 'corridor.tmx'
        self.room_notifier.show(Path(initial_tmx).stem)

        # Фоновий трек
        self.music = MusicManager(volume=0.3)
        self.music.load('music/A_Walk_Along_the_Gates.mp3')
        self.music.play(loops=-1)

        # Інвентар
        self.inventory = Inventory()

        # Меню паузи
        font_choices = {
            'title': str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
            'item':  str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
        }
        self.menu = Menu(self.display, font_choices, border_thickness=2)

        # Спрайт‐групи
        self.all_sprites      = CameraGroup()
        self.collision_sprites= pygame.sprite.Group()
        self.item_sprites     = pygame.sprite.Group()
        self.door_sprites     = pygame.sprite.Group()

        # Завантажити карту та побудувати світ
        self.tmx = ResourceManager.load_tmx(initial_tmx)
        self.setup()

        # Зареєструвати стікери в інвентарі
        for png in STICKERS_DIR.glob('*.png'):
            rel = png.relative_to(PARENT_DIR)
            surf = ResourceManager.load_image(rel)
            self.inventory.register_item(png.stem, surf)

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
        # Очистити всі групи
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_sprites.empty()
        self.door_sprites.empty()

        # Малюємо шари землі
        for layer in ['Ground', 'Ground_layer1','Ground_layer2','Ground_layer3','Ground_layer4']:
            for x, y, img in self.tmx.get_layer_by_name(layer).tiles():
                WorldSprite((x*TILE_SIZE, y*TILE_SIZE), img, [self.all_sprites], ground=True)

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

        # Інші об’єкти
        for obj in self.tmx.get_layer_by_name('Objects'):
            if getattr(obj, 'gid', 0):
                continue
            if obj.name:
                path = f'data/graphics/objects/{obj.name}.png'
                WorldSprite((obj.x, obj.y), path, [self.all_sprites, self.collision_sprites])

        # Колізійні блоки
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0,0,0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # Двері
        for obj in self.tmx.get_layer_by_name('Doors'):
            if obj.type != 'Door':
                continue
            door = pygame.sprite.Sprite(self.all_sprites, self.door_sprites)
            door.image = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
            door.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            door.target_map = obj.properties.get('target')
            sx = obj.properties.get('spawn_x')
            sy = obj.properties.get('spawn_y')
            door.spawn_pos = (int(sx), int(sy)) if sx is not None and sy is not None else None

        # Обчислюємо досяжні клітини
        free = set()
        w, h = self.tmx.width, self.tmx.height
        for tx in range(w):
            for ty in range(h):
                cell = pygame.Rect(tx*TILE_SIZE, ty*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not any(col.rect.colliderect(cell) for col in self.collision_sprites):
                    free.add((tx, ty))
        start = (self.player.rect.centerx//TILE_SIZE, self.player.rect.centery//TILE_SIZE)
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

    def change_level(self, map_file, spawn_pos=None):
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_file)
        room = Path(map_file).stem
        self.room_notifier.show(room)
        self.setup()
        if spawn_pos:
            self.player.hitbox_rect.center = spawn_pos
            self.player.rect.center       = spawn_pos
        self.all_sprites.set_target(self.player)
        self.item_manager = ItemManager(
            self.tmx, self.all_sprites, self.item_sprites,
            self.inventory, self.player, self.collision_sprites,
            self.reachable
        )
        self.item_manager.spawn_items()
        self.room_notifier.show(room)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.menu.toggle()

            # Головна логіка лише коли меню закрито
            if not self.menu.is_open:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_i:
                    self.inventory.toggle()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.setup()
                    self.item_manager.spawn_items()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                    hits = pygame.sprite.spritecollide(
                        self.player,
                        self.door_sprites,
                        dokill=False,
                        collided=lambda p, d: p.hitbox_rect.colliderect(d.rect)
                    )
                    if hits:
                        door = hits[0]
                        self.change_level(door.target_map, door.spawn_pos)

            # Передаємо всі події в меню (для Sound & Graphic Settings)
            self.menu.handle_event(e)

    def update(self, dt):
        # Якщо меню відкрито — пауза
        if self.menu.is_open:
            return
        self.item_manager.check_pickups()
        self.all_sprites.update(dt)
        self.room_notifier.update()

    def render(self):
        self.display.fill('black')
        self.all_sprites.draw()
        self.room_notifier.draw()
        self.inventory.render(self.display)
        self.menu.render()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 600
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

if __name__ == "__main__":
    Game().run()
