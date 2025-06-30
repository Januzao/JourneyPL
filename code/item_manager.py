import pygame
from pathlib import Path
from settings import TILE_SIZE, PARENT_DIR, AUDIO_DIR
from resource_manager import ResourceManager
from inventory import Inventory


class Item(pygame.sprite.Sprite):
    """
    Represents a collectible item in the game world.
    """
    def __init__(self, item_id: str, image_path: str, pos: tuple[int, int], groups):
        super().__init__(groups)
        # Load and scale the sprite image
        surf = ResourceManager.load_image(image_path)
        self.image = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=pos)

        # Store identifier for inventory
        self.id = item_id


class ItemManager:
    """
    Manages spawning items from the Tiled map and handling pickups.
    """
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

        # Load pickup sound effect
        sound_path = AUDIO_DIR / 'sounds' / 'item_pick_up.mp3'
        try:
            self.pickup_sound = pygame.mixer.Sound(str(sound_path))
        except Exception:
            self.pickup_sound = None

        # Spawn items from the map
        self.spawn_items()

    def spawn_items(self):
        """
        Spawn collectible items at positions defined in the Tiled map 'Objects' layer.
        """
        try:
            objects_layer = self.tmx.get_layer_by_name('Objects')
        except KeyError:
            return  # No Objects layer present

        for obj in objects_layer:
            image_source = obj.properties.get('source')
            if not image_source:
                continue

            # Resolve the image path relative to the project root
            abs_path = (Path(self.tmx.filename).parent / image_source).resolve()
            try:
                rel_path = abs_path.relative_to(PARENT_DIR)
            except ValueError:
                rel_path = abs_path
            image_path = str(rel_path)

            # Normalize ID for inventory
            raw_id = Path(image_path).stem
            base_id = Inventory.normalize_item_id(raw_id)

            # Skip spawning if already collected
            if base_id in self.inventory.items and self.inventory.items[base_id].picked:
                continue

            # Create the item sprite
            Item(base_id, image_path, (obj.x, obj.y), [self.all_sprites, self.item_sprites])

    def check_pickups(self):
        """
        Detect collisions between player and items, update inventory, and play pickup sound.
        """
        hits = pygame.sprite.spritecollide(self.player, self.item_sprites, dokill=True)
        for item in hits:
            # Add to inventory
            self.inventory.pickup_item(item.id)
            # Play sound if available
            if self.pickup_sound:
                self.pickup_sound.play()
