# item_manager.py

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
            inventory: Inventory,
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

        # === Звук підбирання предметів ===
        pickup_path = Path(PARENT_DIR) / 'data' / 'audio' / 'sounds' / 'item_pick_up.mp3'
        try:
            self.pickup_sound = pygame.mixer.Sound(str(pickup_path))
        except Exception:
            self.pickup_sound = None

    def spawn_items(self):
        """Spawn collectible items at positions defined in the Tiled map Objects layer."""
        try:
            objects_layer = self.tmx.get_layer_by_name('Objects')
        except KeyError:
            return  # якщо шару немає

        for obj in objects_layer:
            gid = getattr(obj, 'gid', 0)
            if gid == 0:
                continue
            props = self.tmx.tile_properties.get(gid, {})
            image_source = props.get('source')
            if not image_source:
                continue
            image_path_abs = (Path(self.tmx.filename).parent / image_source).resolve()
            try:
                rel_path = image_path_abs.relative_to(PARENT_DIR)
            except ValueError:
                rel_path = image_path_abs
            image_path = str(rel_path)
            raw_id = Path(image_path).stem
            base_id = Inventory.normalize_item_id(raw_id)
            # пропустити, якщо вже підібрано
            if base_id in self.inventory.items and self.inventory.items[base_id]['picked']:
                continue
            Item(base_id, image_path, (obj.x, obj.y), [self.all_sprites, self.item_sprites])

    def check_pickups(self):
        hits = pygame.sprite.spritecollide(self.player, self.item_sprites, dokill=True)
        for item in hits:
            dx = item.rect.centerx - self.player.rect.centerx
            dy = item.rect.centery - self.player.rect.centery
            if dx * dx + dy * dy <= PICKUP_RADIUS ** 2:
                self.inventory.pickup_item(item.id)
                # === Програти звук підбирання ===
                if self.pickup_sound:
                    self.pickup_sound.play()
            else:
                self.item_sprites.add(item)
