import pygame
from pygame.math import Vector2
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
        # Initialize Pygame and audio
        pygame.init()
        pygame.mixer.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # Background music
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

        # Load the first map (map.tmx)
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'map.tmx')

        # Build world, player, and reachable set
        self.setup()

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

        # Draw ground layers
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

        # Create the player from the 'Entities' layer
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
                # skip tile-objects here
                continue
            if obj.name:
                path = f"data/graphics/objects/{obj.name}.png"
                WorldSprite(
                    (obj.x, obj.y),
                    path,
                    [self.all_sprites, self.collision_sprites]
                )

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

            # Cast properties to int before doing math
            raw_sx = obj.properties.get('spawn_x')
            raw_sy = obj.properties.get('spawn_y')
            if raw_sx is not None and raw_sy is not None:
                sx = int(raw_sx)
                sy = int(raw_sy)
                # px = sx * TILE_SIZE + TILE_SIZE // 2
                # py = sy * TILE_SIZE + TILE_SIZE // 2
                door.spawn_pos = (sx, sy)
            else:
                door.spawn_pos = None

        # Compute reachable floor tiles via BFS
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
        # 1) Load the next map
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / map_filename)
        # 2) Rebuild world & player & doors & collisions
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

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_i:
                    self.inventory.toggle()

                elif e.key == pygame.K_e:
                    # Check for door collision
                    hits = pygame.sprite.spritecollide(
                        self.player,
                        self.door_sprites,
                        dokill=False,
                        collided=lambda p, d: p.hitbox_rect.colliderect(d.rect)
                    )
                    if hits:
                        door = hits[0]
                        self.change_level(door.target_map, door.spawn_pos)

    def update(self, dt):
        # Pickup items, update sprites
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
