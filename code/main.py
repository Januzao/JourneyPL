from __future__ import annotations
import os
import sys
from collections import deque
from pathlib import Path

import pygame
import cv2
from pygame.math import Vector2

from settings import *                # SPRITES_DIR, PARENT_DIR, MAPS_DIR, STICKERS_DIR, TILE_SIZE, тощо
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
from transition import *


class VideoBackground:
    """Відтворює вказане відео в циклі як фон через OpenCV."""
    def __init__(self, rel_path: str, screen: pygame.Surface):
        video_path = Path(PARENT_DIR) / rel_path
        if not video_path.exists():
            raise FileNotFoundError(f"Не знайдено відео: {video_path}")
        self.cap = cv2.VideoCapture(str(video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Не вдалося відкрити відео: {video_path}")
        self.target_size = screen.get_size()

    def get_frame(self) -> pygame.Surface:
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return pygame.Surface(self.target_size)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        return pygame.transform.scale(surf, self.target_size)


def run_menu(screen: pygame.Surface) -> str:
    cfg = load_config()
    fps = cfg["fps"]
    clock = pygame.time.Clock()

    # Fade-in overlay
    fade_duration = 1.0                        # seconds for full fade
    fade_alpha    = 255
    fade_surf     = pygame.Surface(screen.get_size()).convert_alpha()
    fade_surf.fill((0, 0, 0))

    # 1) Фон через OpenCV
    bg_video = VideoBackground("data/video/my_intro.mp4", screen)

    # 2) Логотип зверху
    logo_img = pygame.image.load(
        str(Path(PARENT_DIR) / "data/graphics/ui/PL_Journey.png")
    ).convert_alpha()
    logo_w = int(screen.get_width() * 0.4)
    logo_h = int(logo_img.get_height() * (logo_w / logo_img.get_width()))
    logo = pygame.transform.scale(logo_img, (logo_w, logo_h))
    logo_rect = logo.get_rect(midtop=(screen.get_width() // 2, 20))

    # 3) Ініціюємо Game для доступу до Menu та fullscreen-параметра
    game = Game()
    game.display = screen
    game.menu.display = screen

    # 4) Налаштування пунктів головного меню
    option_keys = ["Play", "Settings", "How to play", "Fullscreen", "Exit"]
    menu_font = pygame.font.Font(
        str(Path(PARENT_DIR) / "data/fonts/ANDYB.TTF"), 48
    )
    spacing = 10
    count = len(option_keys)
    total_h = count * menu_font.get_height() + (count - 1) * spacing
    start_y = screen.get_height() - total_h - 150

    # 5) Звук наведення, обводка
    hover_sound = pygame.mixer.Sound(
        str(Path(PARENT_DIR) / "data/audio/sounds/hover.mp3")
    )
    prev_hover = None
    outline_th = 2

    # --- функція показу How to play ---
    # --- функція показу How to play з заокругленими кутами ---
    def show_how_to_play():
        img_path = Path(PARENT_DIR) / "data/graphics/ui/how_to_play.png"
        if not img_path.exists():
            return
        # 1) Завантажуємо оригінал
        orig = pygame.image.load(str(img_path)).convert_alpha()

        # 2) Масштабуємо у 50% від початкового
        ow, oh = orig.get_size()
        scale = 0.5
        tw, th = int(ow * scale), int(oh * scale)
        img = pygame.transform.smoothscale(orig, (tw, th))

        # 3) Рендеримо маску з заокругленими кутами
        radius = 20
        mask = pygame.Surface((tw, th), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, tw, th), border_radius=radius)
        rounded = pygame.Surface((tw, th), pygame.SRCALPHA)
        rounded.blit(img, (0, 0))
        rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # 4) Центруємо поверх меню
        sw, sh = screen.get_size()
        pos = ((sw - tw) // 2, (sh - th) // 2)

        # 5) Відображаємо до ESC або кліка
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    return

            # — перемальовуємо фон меню позаду —
            screen.blit(bg_video.get_frame(), (0, 0))
            screen.blit(logo, logo_rect)
            for i, text in enumerate(option_texts):
                color = (255,255,0) if i==hovered else (255,255,255)
                rect = option_rects[i]
                # обвідка
                for dx in range(-outline_th, outline_th+1):
                    for dy in range(-outline_th, outline_th+1):
                        if dx==0 and dy==0: continue
                        o_surf = menu_font.render(text, True, (0,0,0))
                        o_rect  = o_surf.get_rect(center=(rect.centerx+dx, rect.centery+dy))
                        screen.blit(o_surf, o_rect)
                t_surf = menu_font.render(text, True, color)
                screen.blit(t_surf, t_surf.get_rect(center=rect.center))

            # — малюємо заокруглену картинку —
            screen.blit(rounded, pos)

            pygame.display.flip()
            clock.tick(fps)


    while True:
        # 0) Compute delta time for fade
        dt = clock.tick(fps) / 1000.0

        # Динамічно формуємо відображувані тексти та їхні rect
        option_texts = []
        option_rects = []
        for i, key in enumerate(option_keys):
            if key == "Fullscreen":
                text = f"Fullscreen: {'On' if game.fullscreen else 'Off'}"
            else:
                text = key
            option_texts.append(text)

            w, h = menu_font.size(text)
            rect = pygame.Rect(0, 0, w, h)
            rect.center = (
                screen.get_width() // 2,
                start_y + i * (h + spacing)
            )
            option_rects.append(rect)

        # Визначаємо hovered-індекс
        mx, my = pygame.mouse.get_pos()
        hovered = next(
            (i for i, r in enumerate(option_rects) if r.collidepoint(mx, my)),
            None
        )
        if hovered is not None and hovered != prev_hover:
            hover_sound.play()
        prev_hover = hovered

        # Обробка подій
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                if game.menu.is_open:
                    game.menu.toggle()
                else:
                    return "quit"

            if game.menu.is_open:
                game.menu.handle_event(e)
                continue

            # Мишка
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and hovered is not None:
                key = option_keys[hovered]
                if key == "Play":
                    return "investigation"
                if key == "Exit":
                    return "quit"
                if key == "Settings":
                    game.menu.toggle()
                if key == "How to play":
                    show_how_to_play()
                if key == "Fullscreen":
                    game.fullscreen = not game.fullscreen
                    width, height = screen.get_size()
                    flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED | (
                        pygame.FULLSCREEN if game.fullscreen else 0
                    )
                    screen = pygame.display.set_mode((width, height), flags)
                    game.display = screen
                    game.menu.display = screen
                    save_config({
                        "resolution": [width, height],
                        "fps": fps,
                        "fullscreen": game.fullscreen,
                    })
                continue

            # Клавіатура (Enter)
            if (e.type == pygame.KEYDOWN and
                e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and
                hovered is not None):
                key = option_keys[hovered]
                if key == "Play":
                    return "investigation"
                if key == "Exit":
                    return "quit"
                if key == "Settings":
                    game.menu.toggle()
                if key == "How to play":
                    show_how_to_play()
                if key == "Fullscreen":
                    game.fullscreen = not game.fullscreen
                    width, height = screen.get_size()
                    flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED | (
                        pygame.FULLSCREEN if game.fullscreen else 0
                    )
                    screen = pygame.display.set_mode((width, height), flags)
                    game.display = screen
                    game.menu.display = screen
                    save_config({
                        "resolution": [width, height],
                        "fps": fps,
                        "fullscreen": game.fullscreen,
                    })

        # Рендер головного меню / налаштувань
        screen.blit(bg_video.get_frame(), (0, 0))
        screen.blit(logo, logo_rect)

        if game.menu.is_open:
            game.menu.render()
        else:
            for i, text in enumerate(option_texts):
                color = (255, 255, 0) if i == hovered else (255, 255, 255)
                rect = option_rects[i]

                # обводка
                for dx in range(-outline_th, outline_th + 1):
                    for dy in range(-outline_th, outline_th + 1):
                        if dx == 0 and dy == 0:
                            continue
                        o_surf = menu_font.render(text, True, (0, 0, 0))
                        o_rect = o_surf.get_rect(center=(rect.centerx + dx, rect.centery + dy))
                        screen.blit(o_surf, o_rect)

                # текст
                t_surf = menu_font.render(text, True, color)
                t_rect = t_surf.get_rect(center=rect.center)
                screen.blit(t_surf, t_rect)

        # Плавне затухання від чорного
        if fade_alpha > 0:
            fade_alpha -= (255 / fade_duration) * dt
            fade_alpha = max(fade_alpha, 0)
            fade_surf.set_alpha(int(fade_alpha))
            screen.blit(fade_surf, (0, 0))

        pygame.display.flip()


def create_centered_window(size: tuple[int, int], flags: int = 0) -> pygame.Surface:
    os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
    return pygame.display.set_mode(size, flags)


# ---------------------------------------------------------------------
# Core game loop – тепер з діалогом підтвердження Exit
# ---------------------------------------------------------------------
class Game:
    def __init__(self) -> None:
        cfg = load_config()
        width, height = cfg["resolution"]
        self.clock_fps = cfg["fps"]
        self.fullscreen = cfg["fullscreen"]

        pygame.init()
        pygame.mixer.init()

        BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
        flags = BASE_FLAGS | (pygame.FULLSCREEN if self.fullscreen else 0)

        if pygame.display.get_surface() is None:
            self.display = pygame.display.set_mode((width, height), flags)
        else:
            self.display = pygame.display.get_surface()
        pygame.display.set_caption("JourneyPL")

        self.clock = pygame.time.Clock()
        self.running = True

        # --- NEW: flags for exit confirmation
        self.confirm_exit = False
        self.exit_to_menu = False

        self.room_notifier = RoomNotifier(self.display)
        self.room_notifier.show((MAPS_DIR / "corridor.tmx").stem)
        self.door_notifier = DoorNotifier(self.display)
        self.was_touching_door = False

        snd_dir = Path(PARENT_DIR) / "data" / "audio" / "sounds"
        try:
            self.snd_inventory = pygame.mixer.Sound(str(snd_dir / "inventory_open.mp3"))
        except:
            self.snd_inventory = None
        try:
            self.snd_door = pygame.mixer.Sound(str(snd_dir / "door_open.mp3"))
        except:
            self.snd_door = None

        font_choices = {
            "title": str(Path(PARENT_DIR) / "data" / "fonts" / "ANDYB.TTF"),
            "item": str(Path(PARENT_DIR) / "data" / "fonts" / "ANDYB.TTF"),
        }
        self.menu = Menu(self.display, font_choices, border_thickness=2)
        try: self.menu.sel_res = self.menu.res_list.index((width, height))
        except:  self.menu.sel_res = 0
        try: self.menu.sel_fps = self.menu.fps_list.index(self.clock_fps)
        except:  self.menu.sel_fps = 1
        self.menu.fullscreen = self.fullscreen

        self.music = MusicManager(volume=0.3)
        self.music.load("A_Walk_Along_the_Gates.mp3")
        self.music.play(loops=-1)

        self.inventory = Inventory()
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()

        self.tmx = ResourceManager.load_tmx(MAPS_DIR / "corridor.tmx")
        self.setup()

        for png_path in STICKERS_DIR.glob("*.png"):
            surf = ResourceManager.load_image(png_path.relative_to(PARENT_DIR))
            self.inventory.register_item(png_path.stem, surf)

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

        self.transition = None
        self.pending_level = None
        self.pending_spawn = None

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

    def change_level(self, map_file: str, spawn_pos: tuple[int, int] | None) -> None:
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_file)
        from pathlib import Path
        room = Path(map_file).stem
        if self.snd_door:
            self.snd_door.play()
        self.room_notifier.show(room)
        self.setup()
        if spawn_pos:
            self.player.hitbox_rect.center = spawn_pos
            self.player.rect.center = spawn_pos
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

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.exit_to_menu = False
                return

            if self.confirm_exit:
                W, H = self.display.get_size()
                dw, dh = 400, 200
                dx, dy = (W - dw) // 2, (H - dh) // 2
                yes_rect = pygame.Rect(dx + 50, dy + dh - 70, 120, 50)
                no_rect = pygame.Rect(dx + dw - 170, dy + dh - 70, 120, 50)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.confirm_exit = False
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if yes_rect.collidepoint(mx, my):
                        self.exit_to_menu = True
                        self.running = False
                    elif no_rect.collidepoint(mx, my):
                        self.confirm_exit = False
                        self.menu.toggle()
                    return

                return

            if self.menu.is_open:
                self.menu.handle_event(event)
                if self.menu.exit_selected:
                    self.menu.exit_selected = False
                    self.confirm_exit = True
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.menu.toggle()
                continue

            if not self.menu.is_open and not self.transition:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                    self.inventory.toggle()
                    if self.snd_inventory:
                        self.snd_inventory.play()
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.setup()
                    self.item_manager.spawn_items()
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
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
                        self.pending_level = door.target_map
                        self.pending_spawn = door.spawn_pos
                        self.transition = HorizontalRectangleSwipeTransition()
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.inventory.handle_event(event)
            self.menu.handle_event(event)

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
                    "fullscreen": self.fullscreen,
                })

            new_fps = self.menu.fps_list[self.menu.sel_fps]
            if new_fps != self.clock_fps:
                self.clock_fps = new_fps
                save_config({
                    "resolution": list(self.display.get_size()),
                    "fps": self.clock_fps,
                    "fullscreen": self.fullscreen,
                })

    def update(self, dt: float) -> None:
        if self.menu.is_open or self.confirm_exit:
            return

        self.item_manager.check_pickups()
        self.all_sprites.update(dt)

        if self.transition:
            self.transition.update(dt)
            if not self.transition.is_transitioning():
                self.change_level(self.pending_level, self.pending_spawn)
                self.transition = None
                self.pending_level = None
                self.pending_spawn = None
            return

        self.item_manager.check_pickups()
        self.all_sprites.update(dt)

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
        self.room_notifier.update()

    def render(self) -> None:
        self.display.fill('black')
        self.all_sprites.draw()
        self.room_notifier.draw()
        self.door_notifier.draw()
        self.inventory.render(self.display)
        self.menu.render()

        if self.confirm_exit:
            W, H = self.display.get_size()
            dw, dh = 400, 200
            dx, dy = (W - dw) // 2, (H - dh) // 2

            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.display.blit(overlay, (0, 0))

            dialog_rect = pygame.Rect(dx, dy, dw, dh)
            pygame.draw.rect(self.display, (30, 30, 30), dialog_rect)
            pygame.draw.rect(self.display, (255, 255, 255), dialog_rect, 2)

            font = self.menu.fonts["item"]
            msg = "Exit to main menu?"
            text_surf = font.render(msg, True, (255, 255, 255))
            self.display.blit(
                text_surf,
                (dialog_rect.centerx - text_surf.get_width() // 2,
                 dialog_rect.top + 40)
            )

            yes_rect = pygame.Rect(dx + 50, dy + dh - 70, 120, 50)
            no_rect = pygame.Rect(dx + dw - 170, dy + dh - 70, 120, 50)
            pygame.draw.rect(self.display, (100, 100, 100), yes_rect)
            pygame.draw.rect(self.display, (100, 100, 100), no_rect)
            pygame.draw.rect(self.display, (255, 255, 255), yes_rect, 2)
            pygame.draw.rect(self.display, (255, 255, 255), no_rect, 2)

            yes_txt = font.render("Yes", True, (255, 255, 255))
            no_txt = font.render("No", True, (255, 255, 255))
            self.display.blit(
                yes_txt,
                (yes_rect.centerx - yes_txt.get_width() // 2,
                 yes_rect.centery - yes_txt.get_height() // 2)
            )
            self.display.blit(
                no_txt,
                (no_rect.centerx - no_txt.get_width() // 2,
                 no_rect.centery - no_txt.get_height() // 2)
            )

        if self.transition:
            self.display.blit(self.transition.image, self.transition.rect)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.clock_fps) / 1500
            self.handle_events()
            self.update(dt)
            self.render()

        if self.exit_to_menu:
            scene = run_menu(self.display)
            if scene == "investigation":
                Game().run()
            elif scene == "settings":
                game = Game()
                game.menu.toggle()
                game.run()
            elif scene == "quit":
                pygame.quit()
                sys.exit()
        else:
            pygame.quit()


# ---------------------------------------------------------------------
# Program entry-point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    pygame.init()
    cfg = load_config()
    width, height = cfg["resolution"]
    fullscreen = cfg["fullscreen"]

    BASE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
    flags = BASE_FLAGS | (pygame.FULLSCREEN if fullscreen else 0)

    os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
    screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Game")

    scene = run_menu(screen)

    if scene == "investigation":
        Game().run()
    elif scene == "settings":
        game = Game()
        game.menu.toggle()
        game.run()
    elif scene == "quit":
        pygame.quit()
        sys.exit()
