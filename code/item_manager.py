import pygame
import random
import hashlib
from pathlib import Path
from settings import PICKUP_RADIUS, TILE_SIZE, PARENT_DIR
from resource_manager import ResourceManager

class Item(pygame.sprite.Sprite):
    def __init__(self, item_id: str, image_path: str, pos: tuple[int,int], groups):
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
        inventory,
        player: pygame.sprite.Sprite,
        collision_sprites: pygame.sprite.Group,
        reachable: set[tuple[int,int]]
    ):
        self.tmx               = tmx
        self.all_sprites       = all_sprites
        self.item_sprites      = item_sprites
        self.inventory         = inventory
        self.player            = player
        self.collision_sprites = collision_sprites
        self.reachable         = reachable

    def spawn_items(self):
        png_files = sorted((Path(PARENT_DIR) / 'data' / 'graphics' / 'stickers').glob('*.png'))
        if not png_files:
            return

        # Збираємо всі тайли підлоги (Ground + Ground_items)
        floor = set()
        for layer_name in ('Ground', 'Ground_items'):
            for tx, ty, _ in self.tmx.get_layer_by_name(layer_name).tiles():
                floor.add((tx, ty))

        # Відфільтровуємо ті, що не колізійні
        free = []
        for tx, ty in floor:
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if not any(col.rect.colliderect(rect) for col in self.collision_sprites):
                free.append((tx, ty))

        if len(free) < len(png_files):
            print("У вас менше вільних тайлів, ніж стікерів!")
            # можна спавнити циклічно або пропускати...

        # Детерміністичне перемішування
        import hashlib, random
        name = Path(self.tmx.filename).name
        seed = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
        rnd = random.Random(seed)
        rnd.shuffle(free)

        # Беремо перші N тайлів — N = кількість PNG
        chosen = free[:len(png_files)]

        # Створюємо спрайти та реєструємо в інвентарі
        for png, (tx, ty) in zip(png_files, chosen):
            pos = (tx * TILE_SIZE, ty * TILE_SIZE)
            path = str(png)
            Item(png.stem, path, pos, [self.all_sprites, self.item_sprites])
            surf = ResourceManager.load_image(path)
            self.inventory.register_item(png.stem, surf)

    def check_pickups(self):
        hits = pygame.sprite.spritecollide(self.player, self.item_sprites, dokill=True)
        for item in hits:
            dx = item.rect.centerx - self.player.rect.centerx
            dy = item.rect.centery  - self.player.rect.centery
            if dx*dx + dy*dy <= PICKUP_RADIUS**2:
                self.inventory.pickup_item(item.id)
            else:
                # повернути назад, якщо занадто далеко
                self.item_sprites.add(item)
