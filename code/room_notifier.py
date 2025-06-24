import pygame
from pathlib import Path
from resource_manager import ResourceManager
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, PARENT_DIR


class RoomNotifier:
    """Показує назву кімнати текстом із чорним обводом над персонажем."""
    DISPLAY_TIME = 5000   # загальний час показу, мс
    FADE_DELAY  = 2000    # час до початку фейду, мс
    FADE_TIME   = DISPLAY_TIME - FADE_DELAY  # тривалість фейду

    def __init__(self, display_surface: pygame.Surface):
        self.display = display_surface
        self.active = False
        self.start_time = 0
        self.text_surf = None
        self.text_rect = None

        # Шрифт 96pt
        font_path = Path(PARENT_DIR) / 'data' / 'fonts' / 'ANDYB.TTF'
        self.font = pygame.font.Font(str(font_path), 96)

    def show(self, room_name: str):
        """Створити текст з stroke і запустити таймер."""
        # Рендер основного білого шару
        white_surf = self.font.render(room_name, True, (255, 255, 255)).convert_alpha()

        # Рендер чорного шару обводу
        # Створюємо поверхню трохи більшу, щоб вистачило місця на обвід
        stroke_width = 2
        w, h = white_surf.get_size()
        surf = pygame.Surface((w + stroke_width*2, h + stroke_width*2), pygame.SRCALPHA)

        # Малюємо чорний контур навколо: зміщуємо текст на всі боки
        for dx in (-stroke_width, 0, stroke_width):
            for dy in (-stroke_width, 0, stroke_width):
                if dx == 0 and dy == 0:
                    continue
                surf.blit(self.font.render(room_name, True, (0, 0, 0)), (dx + stroke_width, dy + stroke_width))

        # Накладаємо білий текст зверху
        surf.blit(white_surf, (stroke_width, stroke_width))

        # Зберігаємо поверхню та прямокутник
        self.text_surf = surf
        disp_rect = self.display.get_rect()
        # Центруємо по X, піднімаємо над центром екрану на 100 px
        self.text_rect = surf.get_rect(midbottom=(disp_rect.centerx, disp_rect.centery - 100))

        # Вмикаємо показ
        self.text_surf.set_alpha(255)
        self.start_time = pygame.time.get_ticks()
        self.active = True

    def update(self):
        """Керує фейдом і вимикає по завершенню."""
        if not self.active:
            return

        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.DISPLAY_TIME:
            self.active = False
        elif elapsed > self.FADE_DELAY:
            fade_elapsed = elapsed - self.FADE_DELAY
            alpha = int(255 * (1 - fade_elapsed / self.FADE_TIME))
            self.text_surf.set_alpha(max(alpha, 0))

    def draw(self):
        """Малює текст, якщо активний."""
        if self.active and self.text_surf:
            self.display.blit(self.text_surf, self.text_rect)
