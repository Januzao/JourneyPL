"""Main entry‑point for the game.

This version integrates the **start menu** taken from `menu_1.py` while
preserving the original game loop implemented in the `Game` class.  At
launch we first show the menu (logo screen); when the player presses
**Enter**, the program seamlessly transitions into the full game.

Key points
----------
*   **create_centered_window()** – helper that positions the Pygame
    window in the centre of the monitor using the `SDL_VIDEO_WINDOW_POS`
    environment variable.
*   **run_menu()** is imported from *menu.py* (added there from
    `menu_1.py`).  It returns either "investigation" (to start the game)
    or "quit" (to exit).
*   Constants `WELCOME_WIDTH/WELCOME_HEIGHT` come from *settings.py*.
*   The original `Game` class is unchanged; all heavy‑lifting happens
    inside it just as before.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Built‑ins & stdlib
# ---------------------------------------------------------------------
import os
import sys
from collections import deque

# ---------------------------------------------------------------------
# Third‑party
# ---------------------------------------------------------------------
import pygame
from pygame.math import Vector2

# ---------------------------------------------------------------------
# Local imports (engine & content)
# ---------------------------------------------------------------------
from settings import *  # noqa: F401,F403 – game relies on many constants
from config import load_config, save_config
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from inventory import Inventory
from item_manager import ItemManager
from music_manager import MusicManager
from room_notifier import RoomNotifier
from door_notifier import DoorNotifier
from menu import Menu

# ---------------------------------------------------------------------
# Start menu logic (was missing from menu.py; now inlined here) -------
# ---------------------------------------------------------------------

# main.py: run_menu пример (используем существующий screen)
def run_menu(screen: pygame.Surface) -> str:
    background = pygame.image.load(str(SPRITES_DIR / "PL_background_1.jpg")).convert()
    logo = pygame.image.load(str(SPRITES_DIR / "new_logo_1.png")).convert_alpha()
    logo = pygame.transform.scale(logo, (600, 375))

    W, H = screen.get_size()
    logo_rect = logo.get_rect(center=(W // 2, int(H / 2.5)))

    while True:
        screen.blit(pygame.transform.scale(background, (W, H)), (0, 0))
        screen.blit(logo, logo_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "investigation"

# ---------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------

def create_centered_window(size: tuple[int, int], flags: int = 0) -> pygame.Surface:
    """Open a Pygame window centred on the primary monitor."""
    # Tell SDL where to place the next window.  Works on Win/Linux.
    os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
    return pygame.display.set_mode(size, flags)


# ---------------------------------------------------------------------
# Core game loop (unchanged from original main.py)
# ---------------------------------------------------------------------

class Game:
    """Encapsulates the entire game state and its main loop."""

    def __init__(self) -> None:
        # 1) Загрузка настроек
        cfg = load_config()
        width, height = cfg["resolution"]
        self.clock_fps = cfg["fps"]
        self.fullscreen = cfg["fullscreen"]

        # 2) Инициализация Pygame (если ещё не вызвано)
        pygame.init()
        pygame.mixer.init()

        # Флаги для дисплея
        BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
        flags = BASE_FLAGS | (pygame.FULLSCREEN if self.fullscreen else 0)

        # Если окно уже существует, используем его; иначе создаем новое
        if pygame.display.get_surface() is None:
            self.display = pygame.display.set_mode((width, height), flags)
        else:
            self.display = pygame.display.get_surface()
        pygame.display.set_caption("JourneyPL")

        # 3) Timers & state flags
        self.clock = pygame.time.Clock()
        self.running = True

        # 4) Room & door notifiers
        self.room_notifier = RoomNotifier(self.display)
        from pathlib import Path  # local import to avoid top‑level cycle
        initial_tmx = MAPS_DIR / 'corridor.tmx'
        self.room_notifier.show(Path(initial_tmx).stem)

        self.door_notifier = DoorNotifier(self.display)
        self.was_touching_door = False

        # 5) Load UI sounds (hover, inventory, door)
        snd_dir = Path(PARENT_DIR) / 'data' / 'audio' / 'sounds'
        try:
            self.snd_inventory = pygame.mixer.Sound(str(snd_dir / 'inventory_open.mp3'))
        except Exception:
            self.snd_inventory = None
        try:
            self.snd_door = pygame.mixer.Sound(str(snd_dir / 'door_open.mp3'))
        except Exception:
            self.snd_door = None

        # 6) Pause / settings menu (the in‑game ESC menu)
        font_choices = {
            'title': str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
            'item': str(Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'),
        }
        self.menu = Menu(self.display, font_choices, border_thickness=2)

        # Reflect current config in the menu widgets
        try:
            self.menu.sel_res = self.menu.res_list.index((width, height))
        except ValueError:
            self.menu.sel_res = 0
        try:
            self.menu.sel_fps = self.menu.fps_list.index(self.clock_fps)
        except ValueError:
            self.menu.sel_fps = 1
        self.menu.fullscreen = self.fullscreen

        # 7) Music
        self.music = MusicManager(volume=0.3)
        self.music.load('A_Walk_Along_the_Gates.mp3')
        self.music.play(loops=-1)

        # 8) Gameplay systems ------------------------------------------------
        #    (world, player, collectibles, etc.)

        # Inventory UI
        self.inventory = Inventory()

        # Sprite groups
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()

        # Load the first map (corridor.tmx)
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'corridor.tmx')

        # Build the world and position the player
        self.setup()

        # Pre‑register sticker slots in the inventory
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
            self.reachable,
        )
        self.item_manager.spawn_items()

    # ------------------------------------------------------------------
    # World / level construction helpers
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """(Re)builds the current map – tiles, objects, doors, player."""
        # Clear previous contents
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_sprites.empty()
        self.door_sprites.empty()

        # --- GROUND LAYERS ------------------------------------------------
        for layer in ['Ground', 'Ground_layer1', 'Ground_layer2', 'Ground_layer3', 'Ground_layer4']:
            for x, y, img in self.tmx.get_layer_by_name(layer).tiles():
                WorldSprite((x * TILE_SIZE, y * TILE_SIZE), img, [self.all_sprites], ground=True)

        # --- PLAYER -------------------------------------------------------
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    Vector2(obj.x, obj.y),
                    [self.all_sprites],
                    self.collision_sprites,
                )
                self.all_sprites.set_target(self.player)
                break

        # --- STATIC OBJECTS ----------------------------------------------
        for obj in self.tmx.get_layer_by_name('Objects'):
            if getattr(obj, 'gid', 0):
                continue  # Skip tile objects
            if obj.name:
                path = f"data/graphics/objects/{obj.name}.png"
                WorldSprite((obj.x, obj.y), path, [self.all_sprites, self.collision_sprites])

        for obj in self.tmx.get_layer_by_name('Ground_objects'):
            if getattr(obj, 'gid', 0):
                continue
            if obj.name:
                path = f"data/graphics/objects/{obj.name}.png"
                WorldSprite((obj.x, obj.y), path, [self.all_sprites, self.collision_sprites])

        # --- COLLISION SHAPES --------------------------------------------
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0, 0, 0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # --- DOOR TRIGGERS ------------------------------------------------
        for obj in self.tmx.get_layer_by_name('Doors'):
            if obj.type != 'Door':
                continue
            door = pygame.sprite.Sprite(self.all_sprites, self.door_sprites)
            door.image = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
            door.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            door.target_map = obj.properties.get('target')
            raw_sx = obj.properties.get('spawn_x')
            raw_sy = obj.properties.get('spawn_y')
            door.spawn_pos = (int(raw_sx), int(raw_sy)) if raw_sx is not None and raw_sy is not None else None

        # --- REACHABLE CELLS ---------------------------------------------
        free: set[tuple[int, int]] = set()
        w, h = self.tmx.width, self.tmx.height
        for tx in range(w):
            for ty in range(h):
                cell = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not any(col.rect.colliderect(cell) for col in self.collision_sprites):
                    free.add((tx, ty))
        start = (
            self.player.rect.centerx // TILE_SIZE,
            self.player.rect.centery // TILE_SIZE,
        )
        reachable = {start}
        queue: deque[tuple[int, int]] = deque([start])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nb = (cx + dx, cy + dy)
                if nb in free and nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)
        self.reachable = reachable

    # ------------------------------------------------------------------
    # Level switcher
    # ------------------------------------------------------------------

    def change_level(self, map_file: str, spawn_pos: tuple[int, int] | None) -> None:
        """Loads *map_file* and puts the player at *spawn_pos* if provided."""
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_file)
        from pathlib import Path
        room = Path(map_file).stem
        if self.snd_door:
            self.snd_door.play()
        self.room_notifier.show(room)
        self.setup()
        # Re‑position the player if a spawn coordinate was provided
        if spawn_pos:
            self.player.hitbox_rect.center = spawn_pos
            self.player.rect.center = spawn_pos
        # Retarget camera & respawn collectibles
        self.all_sprites.set_target(self.player)
        self.item_manager = ItemManager(
            self.tmx,
            self.all_sprites,
            self.item_sprites,
            self.inventory,
            self.player,
            self.collision_sprites,
            self.reachable,
        )
        self.item_manager.spawn_items()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_events(self) -> None:
        """Poll & handle Pygame events – input, window, menu, etc."""
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
                        collided=lambda p, d: p.hitbox_rect.colliderect(d.rect),
                    )
                    if hits:
                        door = hits[0]
                        if self.snd_door:
                            self.snd_door.play()
                        self.change_level(door.target_map, door.spawn_pos)
            # Forward mouse events to inventory regardless of menu state
            if e.type == pygame.MOUSEBUTTONDOWN:
                self.inventory.handle_event(e)

            # Let the pause/settings menu handle UI clicks & keyboard
            self.menu.handle_event(e)

            # ----------------------------------------------------------------
            # Resolution / fullscreen changes triggered by the pause menu
            # ----------------------------------------------------------------
            new_res = self.menu.res_list[self.menu.sel_res]
            new_fs = self.menu.fullscreen
            if self.display.get_size() != new_res or new_fs != self.fullscreen:
                BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
                flags = BASE_FLAGS | (pygame.FULLSCREEN if new_fs else 0)
                pygame.display.set_mode(new_res, flags)
                self.display = pygame.display.get_surface()
                # Update references in subsystems
                self.menu.display = self.display
                self.room_notifier.display = self.display
                self.fullscreen = new_fs
                save_config({
                    "resolution": list(new_res),
                    "fps": self.clock_fps,
                    "fullscreen": self.fullscreen,
                })

            # Apply FPS changes
            new_fps = self.menu.fps_list[self.menu.sel_fps]
            if new_fps != self.clock_fps:
                self.clock_fps = new_fps
                save_config({
                    "resolution": list(self.display.get_size()),
                    "fps": self.clock_fps,
                    "fullscreen": self.fullscreen,
                })

    # ------------------------------------------------------------------
    # Update & render
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.menu.is_open:
            return  # Game world is paused while the settings menu is open
        self.item_manager.check_pickups()
        self.all_sprites.update(dt)

        # Door proximity detection (shows banner when touching a door)
        hits = pygame.sprite.spritecollide(
            self.player,
            self.door_sprites,
            dokill=False,
            collided=lambda p, d: p.hitbox_rect.colliderect(d.rect),
        )
        if hits:
            if not self.was_touching_door:
                self.door_notifier.show()
            self.was_touching_door = True
        else:
            self.was_touching_door = False

        # Update banners fade‑outs
        self.room_notifier.update()
        self.door_notifier.update()

    def render(self) -> None:
        self.display.fill('black')
        self.all_sprites.draw()
        self.room_notifier.draw()
        self.door_notifier.draw()
        self.inventory.render(self.display)
        self.menu.render()
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run the main game loop until the window is closed."""
        while self.running:
            dt = self.clock.tick(self.clock_fps) / 600  # Normalise delta
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()


# ---------------------------------------------------------------------
# Program entry‑point – show start menu, then launch the game
# ---------------------------------------------------------------------

# main.py (фрагмент с запуском программы в __main__)
if __name__ == "__main__":
    import os, pygame, sys
    from config import load_config

    pygame.init()
    # Загружаем настройки из config.py
    cfg = load_config()
    width, height = cfg["resolution"]
    fullscreen = cfg["fullscreen"]
    fps = cfg["fps"]

    # Флаги для окна (двойная буферизация, аппаратная поверхность, масштабирование, полноэкранный режим)
    BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
    flags = BASE_FLAGS | (pygame.FULLSCREEN if fullscreen else 0)

    # Центрируем окно (для оконного режима)
    os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
    screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Game")

    # Показываем стартовое меню на этом же Surface
    scene = run_menu(screen)  # Возвращает "investigation" или "quit"

    # Запускаем игру, если выбрано продолжение
    if scene == "investigation":
        Game().run()

    pygame.quit()
    sys.exit()

