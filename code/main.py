import pygame
from pygame.math import Vector2
from collections import deque

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
from menu import Menu

from config import load_config, save_config


class Game:
    def __init__(self):
        # 1) Load settings
        cfg = load_config()
        width, height = cfg["resolution"]
        self.clock_fps = cfg["fps"]
        self.fullscreen = cfg["fullscreen"]

        # 2) Init Pygame & window (with fullscreen flag + scaling/buffering)
        pygame.init()
        pygame.mixer.init()
        BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
        flags = BASE_FLAGS | (pygame.FULLSCREEN if self.fullscreen else 0)
        self.display = pygame.display.set_mode((width, height), flags)
        self.room_notifier = RoomNotifier(self.display)
        self.room_notifier.show(Path(MAPS_DIR / 'corridor.tmx').stem)
        self.door_notifier = DoorNotifier(self.display)
        self.was_touching_door = False

        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- Load SFX ---
        snd_dir = Path(PARENT_DIR) / 'data' / 'audio' / 'sounds'
        try:
            self.snd_inventory = pygame.mixer.Sound(str(snd_dir / 'inventory_open.mp3'))
        except:
            self.snd_inventory = None
        try:
            self.snd_door = pygame.mixer.Sound(str(snd_dir / 'door_open.mp3'))
        except:
            self.snd_door = None

        # 3) Pause menu
        font_choices = {
            'title': str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
            'item': str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
        }
        self.menu = Menu(self.display, font_choices, border_thickness=2)

        # Pass initial settings into menu (including fullscreen)
        try:
            self.menu.sel_res = self.menu.res_list.index((width, height))
        except ValueError:
            self.menu.sel_res = 0
        try:
            self.menu.sel_fps = self.menu.fps_list.index(self.clock_fps)
        except ValueError:
            self.menu.sel_fps = 1
        self.menu.fullscreen = self.fullscreen

        # 4) Other game components
        self.room_notifier = RoomNotifier(self.display)
        initial_tmx = MAPS_DIR / 'corridor.tmx'
        self.room_notifier.show(Path(initial_tmx).stem)

        self.music = MusicManager(volume=0.3)
        self.music.load('A_Walk_Along_the_Gates.mp3')
        self.music.play(loops=-1)

        # Inventory
        self.inventory = Inventory()

        # Sprite groups
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()

        # Загрузка первой карты (corridor.tmx)
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'corridor.tmx')

        # Построение мира, игрока и доступных для движения тайлов
        self.setup()

        # Предрегистрация слотов для наклеек (стикеров)
        for png_path in STICKERS_DIR.glob('*.png'):
            rel = png_path.relative_to(PARENT_DIR)
            surf = ResourceManager.load_image(rel)
            self.inventory.register_item(png_path.stem, surf)

        # Spawn collectibles for the first map
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
        # Clear any previous sprites
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_sprites.empty()
        self.door_sprites.empty()

        # Ground layers
        for layer in ['Ground', 'Ground_layer1', 'Ground_layer2', 'Ground_layer3', 'Ground_layer4']:
            for x, y, img in self.tmx.get_layer_by_name(layer).tiles():
                WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)

        # Player
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    Vector2(obj.x, obj.y),
                    [self.all_sprites],
                    self.collision_sprites
                )
                self.all_sprites.set_target(self.player)
                break

        # Non-collectible Objects
        for obj in self.tmx.get_layer_by_name('Objects'):
            if getattr(obj, 'gid', 0):
                continue
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
                path = f'data/graphics/objects/{obj.name}.png'
                WorldSprite((obj.x, obj.y), path, [self.all_sprites, self.collision_sprites])

        # Collision shapes
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0, 0, 0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # Doors (invisible triggers)
        for obj in self.tmx.get_layer_by_name('Doors'):
            if obj.type != 'Door':
                continue

            door = pygame.sprite.Sprite(self.all_sprites, self.door_sprites)
            door.image = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
            door.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            # Store target map
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

    def change_level(self, map_file, spawn_pos: tuple[int, int] | None):
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_file)
        room = Path(map_file).stem
        if self.snd_door:
            self.snd_door.play()
        self.room_notifier.show(room)
        self.setup()
        # 3) Reposition the player if spawn_pos given
        if spawn_pos:
            self.player.hitbox_rect.center = spawn_pos
            self.player.rect.center = spawn_pos
        # 4) Re‐target camera
        self.all_sprites.set_target(self.player)
        # 5) Respawn collectibles
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
        room_name = Path(map_file).stem
        self.room_notifier.show(room_name)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.menu.toggle()

            if not self.menu.is_open:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_i:
                    self.inventory.toggle()
                    if self.snd_inventory:
                        self.snd_inventory.play()
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
                        if self.snd_door:
                            self.snd_door.play()
                        self.change_level(door.target_map, door.spawn_pos)
            # Передаём нажатия мыши в инвентарь
            if e.type == pygame.MOUSEBUTTONDOWN:
                self.inventory.handle_event(e)

            self.menu.handle_event(e)
            # Apply graphic settings
            new_res = self.menu.res_list[self.menu.sel_res]
            new_fs = self.menu.fullscreen
            if self.display.get_size() != new_res or new_fs != self.fullscreen:
                BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
                flags = BASE_FLAGS | (pygame.FULLSCREEN if new_fs else 0)
                pygame.display.set_mode(new_res, flags)
                self.display = pygame.display.get_surface()
                self.menu.display = self.display
                self.room_notifier.display = self.display
                self.fullscreen = new_fs
                save_config({
                    "resolution": list(new_res),
                    "fps": self.clock_fps,
                    "fullscreen": self.fullscreen
                })

            # Apply FPS
            new_fps = self.menu.fps_list[self.menu.sel_fps]
            if new_fps != self.clock_fps:
                self.clock_fps = new_fps
                save_config({
                    "resolution": list(self.display.get_size()),
                    "fps": self.clock_fps,
                    "fullscreen": self.fullscreen
                })

    def update(self, dt):
        if self.menu.is_open:
            return
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
        self.all_sprites.draw()
        self.room_notifier.draw()
        # Отрисовываем баннер двери (если активен)
        self.door_notifier.draw()
        self.inventory.render(self.display)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(self.clock_fps) / 600
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
