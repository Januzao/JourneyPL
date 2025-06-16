import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE, MAPS_DIR
from resource_manager import ResourceManager
from sprites import WorldSprite
from player import Player
from groups import CameraGroup
from collections import deque


class Game:
    def __init__(self):
        pygame.init()
        pygame.event.get()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("JourneyPL")
        self.clock = pygame.time.Clock()
        self.running = True

        # Групи спрайтів
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

        # Завантажуємо карту
        self.tmx = ResourceManager.load_tmx(MAPS_DIR / 'map.tmx')

        # Ініціалізація світу
        self.setup()

    def setup(self):
        # Очищаємо спрайти
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.item_group.empty()

        # Створюємо землю
        for x, y, img in self.tmx.get_layer_by_name('Ground').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE),
                        img,
                        [self.all_sprites],
                        ground=True)

        for x, y, img in self.tmx.get_layer_by_name('Ground_items').tiles():
            WorldSprite((x * TILE_SIZE, y * TILE_SIZE),
                        img,
                        [self.all_sprites],
                        ground=True)

        # Створюємо видимі об'єкти
        for obj in self.tmx.get_layer_by_name('Objects'):
            WorldSprite((obj.x, obj.y),
                        f'data/graphics/objects/{obj.name}.png',
                        [self.all_sprites, self.collision_sprites])

        # Створюємо невидимі колізії
        for obj in self.tmx.get_layer_by_name('Collisions'):
            surf = pygame.Surface((obj.width, obj.height))
            surf.fill((0, 0, 0))
            WorldSprite((obj.x, obj.y), surf, [self.collision_sprites])

        # Розміщуємо гравця
        for obj in self.tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    pygame.math.Vector2(obj.x, obj.y),
                    [self.all_sprites, self.collision_sprites],
                    self.collision_sprites
                )
                self.all_sprites.set_target(self.player)
                break

        # Збираємо прохідні тайли
        free = set()
        w, h = self.tmx.width, self.tmx.height
        for tx in range(w):
            for ty in range(h):
                rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE,
                                   TILE_SIZE, TILE_SIZE)
                if not any(c.rect.colliderect(rect) for c in self.collision_sprites):
                    free.add((tx, ty))

        # BFS для досяжних тайлів
        start = (self.player.rect.centerx // TILE_SIZE,
                 self.player.rect.centery // TILE_SIZE)
        reachable = {start}
        queue = deque([start])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nb = (cx + dx, cy + dy)
                if nb in free and nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                self.setup()

    def update(self, dt):
        self.all_sprites.update(dt)

    def render(self):
        self.display.fill('black')
        self.all_sprites.draw()
        pygame.display.update()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()


if __name__ == '__main__':
    Game().run()
