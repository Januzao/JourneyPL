import pygame
import random
import hashlib
from pathlib import Path
from settings import PICKUP_RADIUS, TILE_SIZE, PARENT_DIR
from resource_manager import ResourceManager
from inventory import Inventory


class Item(pygame.sprite.Sprite):
    def __init__(self, item_id: str, image_path: str, pos: tuple[int, int], groups):
        super().__init__(groups)
        # Load and scale the sprite image
        surf = ResourceManager.load_image(image_path)
        self.image = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.id = item_id


class ItemManager:
    def __init__(
        self,
        tmx,
        all_sprites: pygame.sprite.Group,
        item_sprites: pygame.sprite.Group,
        inventory,
        player: pygame.sprite.Sprite,
        collision_sprites: pygame.sprite.Group,
        reachable: set[tuple[int, int]]
    ):
        self.tmx = tmx
        self.all_sprites = all_sprites
        self.item_sprites = item_sprites
        self.inventory = inventory
        self.player = player
        self.collision_sprites = collision_sprites
        self.reachable = reachable

    def spawn_items(self):
        """Spawn collectible items at positions defined in the Tiled map 'Objects' layer."""
        try:
            objects_layer = self.tmx.get_layer_by_name('Objects')
        except KeyError:
            return  # No Objects layer present

        for obj in objects_layer:
            gid = getattr(obj, 'gid', None)
            if gid is None or gid == 0:
                continue

            props = self.tmx.tile_properties.get(gid, {})
            image_source = props.get('source')
            if not image_source:
                continue

            # Resolve the image path relative to the project root
            image_path_abs = (Path(self.tmx.filename).parent / image_source).resolve()
            try:
                rel_path = image_path_abs.relative_to(PARENT_DIR)
            except ValueError:
                rel_path = image_path_abs
            image_path = str(rel_path)

            raw_id = Path(image_path).stem  # e.g. "sticker_1_64x64"
            base_id = Inventory.normalize_item_id(raw_id)  # -> "sticker_1"

            # Skip spawning if already collected
            if base_id in self.inventory.items and self.inventory.items[base_id].picked:
                continue

            # Create the item sprite
            Item(base_id, image_path, (obj.x, obj.y), [self.all_sprites, self.item_sprites])

    def check_pickups(self):
        """Detect collisions between player and items, update inventory."""
        hits = pygame.sprite.spritecollide(self.player, self.item_sprites, dokill=True)
        for item in hits:
            self.inventory.pickup_item(item.id)
