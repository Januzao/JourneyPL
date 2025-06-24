# main.py
import pygame
from pygame.math import Vector2
from collections import deque
from pathlib import Path

from settings import *
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from inventory import Inventory
from item_manager import ItemManager
from music_manager import MusicManager
from room_notifier import RoomNotifier
from door_notifier import DoorNotifier  # импортируем DoorNotifier


class Game:
    def __init__(self):
        # Инициализация Pygame и аудио
        pygame.init()
        pygame.mixer.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        # Инициализация баннера комнат и показываем стартовый (при необходимости)
        self.room_notifier = RoomNotifier(self.display)
        self.room_notifier.show(Path(MAPS_DIR / 'corridor.tmx').stem)

        # Инициализация баннера двери
        self.door_notifier = DoorNotifier(self.display)
        # Флаг, показывающий, был ли контакт с дверью на прошлом кадре
        self.was_touching_door = False

        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # Фоновая музыка
        self.music = MusicManager(volume=0.3)
        self.music.load('A_Walk_Along_the_Gates.mp3')
        self.music.play(loops=-1)

        # Инвентарь
        self.inventory = Inventory()

        # Группы спрайтов
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()

        # Загрузка первой карты (corridor.tmx)
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'corridor.tmx')

        # Построение мира, игрока и доступных для движения тайлов
        self.setup()

        # Предрегистрация слотов для наклеек (стикеров)
        stickers_dir = STICKERS_DIR
        for png_path in stickers_dir.glob('*.png'):
            rel = png_path.relative_to(PARENT_DIR)
            surf = ResourceManager.load_image(rel)
            self.inventory.register_item(png_path.stem, surf)

        # Спавн коллекционных предметов на первой карте
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
        # Очищаем предыдущие спрайты
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_sprites.empty()
        self.door_sprites.empty()

        # Рисуем слои земли
        for x, y, img in self.tmx.get_layer_by_name('Ground').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)
        for x, y, img in self.tmx.get_layer_by_name('Ground_layer1').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)
        for x, y, img in self.tmx.get_layer_by_name('Ground_layer2').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)
        for x, y, img in self.tmx.get_layer_by_name('Ground_layer3').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)
        for x, y, img in self.tmx.get_layer_by_name('Ground_layer4').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)

        # Создаём игрока из слоя 'Entities'
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    Vector2(obj.x, obj.y),
                    [self.all_sprites],
                    self.collision_sprites
                )
                self.all_sprites.set_target(self.player)
                break

        # Рисуем неподбираемые объекты
        for obj in self.tmx.get_layer_by_name('Objects'):
            if getattr(obj, 'gid', 0):
                continue  # пропускаем тайловые объекты
            if obj.name:
                path = f"data/graphics/objects/{obj.name}.png"
                WorldSprite(
                    (obj.x, obj.y),
                    path,
                    [self.all_sprites, self.collision_sprites]
                )

        for obj in self.tmx.get_layer_by_name('Ground_objects'
                                              ''):
            if getattr(obj, 'gid', 0):
                continue  # пропускаем тайловые объекты
            if obj.name:
                path = f"data/graphics/objects/{obj.name}.png"
                WorldSprite(
                    (obj.x, obj.y),
                    path,
                    [self.all_sprites, self.collision_sprites]
                )

        # Физические коллизии
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0, 0, 0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # Двери (скрытые триггеры)
        for obj in self.tmx.get_layer_by_name('Doors'):
            if obj.type != 'Door':
                continue
            door = pygame.sprite.Sprite(self.all_sprites, self.door_sprites)
            door.image = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
            door.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            door.target_map = obj.properties.get('target')
            raw_sx = obj.properties.get('spawn_x')
            raw_sy = obj.properties.get('spawn_y')
            if raw_sx is not None and raw_sy is not None:
                sx = int(raw_sx);
                sy = int(raw_sy)
                door.spawn_pos = (sx, sy)
            else:
                door.spawn_pos = None

        # Вычисляем достижимые клетки через BFS
        free = set()
        w, h = self.tmx.width, self.tmx.height
        for tx in range(w):
            for ty in range(h):
                cell = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not any(col.rect.colliderect(cell) for col in self.collision_sprites):
                    free.add((tx, ty))
        start = (
            self.player.rect.centerx // TILE_SIZE,
            self.player.rect.centery // TILE_SIZE
        )
        reachable = {start}
        queue = deque([start])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nb = (cx + dx, cy + dy)
                if nb in free and nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)
        self.reachable = reachable

    def change_level(self, map_filename: str, spawn_pos: tuple[int, int] | None):
        # Загрузка следующей карты
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_filename)
        room_name = Path(map_filename).stem
        self.room_notifier.show(room_name)
        self.setup()
        if spawn_pos:
            self.player.hitbox_rect.center = spawn_pos
            self.player.rect.center = spawn_pos
        self.all_sprites.set_target(self.player)
        # Возрождаем предметы
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
        room_name = Path(map_filename).stem
        self.room_notifier.show(room_name)

    def handle_events(self):
        """Обработка входящих событий Pygame."""
        for e in pygame.event.get():
            # Выход из игры
            if e.type == pygame.QUIT:
                self.running = False

            # Клавиши управления
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_i:
                    self.inventory.toggle()

                elif e.key == pygame.K_e:
                    # Взаимодействие с дверью по нажатию клавиши 'E'
                    hits = pygame.sprite.spritecollide(
                        self.player,
                        self.door_sprites,
                        dokill=False,
                        collided=lambda p, d: p.hitbox_rect.colliderect(d.rect)
                    )
                    if hits:
                        door = hits[0]
                        self.change_level(door.target_map, door.spawn_pos)

            # Передаём нажатия мыши в инвентарь
            if e.type == pygame.MOUSEBUTTONDOWN:
                self.inventory.handle_event(e)

    def update(self, dt):
        # Обновляем состояние предметов и спрайтов
        self.item_manager.check_pickups()
        self.all_sprites.update(dt)

        # Проверяем столкновение игрока с дверьми (без нажатий)
        hits = pygame.sprite.spritecollide(
            self.player,
            self.door_sprites,
            dokill=False,
            collided=lambda p, d: p.hitbox_rect.colliderect(d.rect)
        )
        if hits:
            # Если только что коснулись двери – показываем баннер
            if not self.was_touching_door:
                self.door_notifier.show()
            self.was_touching_door = True
        else:
            # Сброс флага, когда игрок отошёл от двери
            self.was_touching_door = False

        # Обновляем анимации баннеров
        self.room_notifier.update()
        self.door_notifier.update()

    def render(self):
        self.display.fill('black')
        self.all_sprites.draw(self.player)
        # Отрисовываем баннер комнаты (если активен)
        self.room_notifier.draw()
        # Отрисовываем баннер двери (если активен)
        self.door_notifier.draw()
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
