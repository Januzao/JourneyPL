import pygame
from pathlib import Path
from settings import *

class Menu:
    def __init__(self, display, font_choices, border_thickness=2):
        self.display = display
        self.font_choices = font_choices
        self.base_resolution = (1920, 1080)
        self.border = border_thickness

        self.is_open = False
        self.in_sound = False
        self.in_graphic = False
        self.open_res = False
        self.open_fps = False
        self.hover = None
        self.exit_selected = False

        # Sound settings
        self.music_vol = 0.5
        self.sfx_vol = 0.5
        self.dragging = None

        # Graphic settings
        pygame.font.init()
        modes = pygame.display.list_modes()
        candidates = [(1280, 720), (1920, 1080), (2560, 1440)]
        self.res_list = [r for r in candidates if r in modes]
        if not self.res_list:
            self.res_list = [self.display.get_size()]
        self.res_strs = [f"{w}x{h}" for w, h in self.res_list]
        self.fps_list = [30, 60, 90, 120, 144]
        self.sel_res = 0
        self.sel_fps = 1  # default to 60
        self.fullscreen = False

        # Prepare scaling and fonts
        self.fonts = {}
        self.update_scale()

        # Main menu items
        self.items = ["Graphic Settings", "Sound Settings", "Achievements", "Exit"]

        # Hover sound
        hover_path = Path(PARENT_DIR) / 'data' / 'audio' / 'sounds' / 'hover.mp3'
        try:
            self.hover_snd = pygame.mixer.Sound(str(hover_path))
            self.hover_snd.set_volume(self.sfx_vol)
        except Exception:
            self.hover_snd = None
        pygame.mixer.music.set_volume(self.music_vol)

    def update_scale(self):
        W, H = self.display.get_size()
        base_w, base_h = self.base_resolution
        self.scale = min(W / base_w, H / base_h)

        # Panel size
        self.pw = max(int(600 * self.scale), 300)
        self.ph = max(int(450 * self.scale), 200)

        # Fonts
        for key, path in self.font_choices.items():
            if key == 'title':
                size = max(int(72 * self.scale), 24)
            else:
                size = max(int(36 * self.scale), 16)
            if path:
                self.fonts[key] = pygame.font.Font(path, size)
            else:
                self.fonts[key] = pygame.font.SysFont(None, size)

    def apply_graphic_settings(self):
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        w, h = self.res_list[self.sel_res]
        self.display = pygame.display.set_mode((w, h), flags)
        self.update_scale()

    def toggle(self):
        self.is_open = not self.is_open
        self.in_sound = False
        self.in_graphic = False
        self.open_res = False
        self.open_fps = False
        self.hover = None

    def handle_event(self, event):
        if not self.is_open:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.in_sound or self.in_graphic or self.open_res or self.open_fps:
                self.in_sound = self.in_graphic = self.open_res = self.open_fps = False
            else:
                self.toggle()
            return

        # Main‐menu clicks
        if event.type == pygame.MOUSEBUTTONDOWN and not (self.in_sound or self.in_graphic):
            if self.hover == 0:
                self.in_graphic = True
                return
            if self.hover == 1:
                self.in_sound = True
                self.dragging = None
                return
            if self.hover == 3:
                self.exit_selected = True
                self.toggle()
                return

        # ENTER on Exit
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if not (self.in_sound or self.in_graphic) and self.hover == 3:
                self.exit_selected = True
                self.toggle()
            return

        # Graphic submenu logic
        if self.in_graphic:
            W, H = self.display.get_size()
            rect = pygame.Rect((W - self.pw)//2, (H - self.ph)//2, self.pw, self.ph)
            box_w = self.pw - int(200 * self.scale)
            box_x = rect.left + (self.pw - box_w)//2
            fi = self.fonts['item']
            ih = fi.get_height() + int(8 * self.scale)
            res_y = rect.top + int(140 * self.scale)
            fps_y = res_y + ih + int(40 * self.scale)
            fs_y  = fps_y + ih + int(40 * self.scale)

            mx, my = None, None
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

            # Toggle resolution dropdown
            if event.type == pygame.MOUSEBUTTONDOWN and not self.open_fps:
                if pygame.Rect(box_x, res_y, box_w, ih).collidepoint(mx, my):
                    self.open_res = not self.open_res
                    self.open_fps = False
                    return
            # Pick a resolution
            if self.open_res and event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(self.res_list)):
                    if pygame.Rect(box_x, res_y + ih*(i+1), box_w, ih).collidepoint(mx, my):
                        self.sel_res = i
                        self.open_res = False
                        self.apply_graphic_settings()
                        return

            # Toggle FPS dropdown
            if event.type == pygame.MOUSEBUTTONDOWN and not self.open_res:
                if pygame.Rect(box_x, fps_y, box_w, ih).collidepoint(mx, my):
                    self.open_fps = not self.open_fps
                    self.open_res = False
                    return
            # Pick an FPS
            if self.open_fps and event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(self.fps_list)):
                    if pygame.Rect(box_x, fps_y + ih*(i+1), box_w, ih).collidepoint(mx, my):
                        self.sel_fps = i
                        self.open_fps = False
                        return

            # Fullscreen toggle
            if not (self.open_res or self.open_fps) and event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(box_x, fs_y, box_w, ih).collidepoint(mx, my):
                    self.fullscreen = not self.fullscreen
                    self.apply_graphic_settings()
                    return
            return

        # Sound submenu logic
        if self.in_sound:
            W, H = self.display.get_size()
            rect = pygame.Rect((W - self.pw)//2, (H - self.ph)//2, self.pw, self.ph)
            box_w = self.pw - int(200 * self.scale)
            box_x = rect.left + (self.pw - box_w)//2
            my_line = rect.top + self.ph//2 - int(50 * self.scale)
            sy_line = my_line + int(100 * self.scale)
            kr = int(10 * self.scale)
            mxk = box_x + int(box_w * self.music_vol)
            sxk = box_x + int(box_w * self.sfx_vol)

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if (x - mxk)**2 + (y - my_line)**2 <= kr**2:
                    self.dragging = 'music'
                if (x - sxk)**2 + (y - sy_line)**2 <= kr**2:
                    self.dragging = 'sfx'
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = None
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                x, _ = event.pos
                rel = max(0, min(x - box_x, box_w)) / box_w
                if self.dragging == 'music':
                    self.music_vol = rel
                    pygame.mixer.music.set_volume(rel)
                else:
                    self.sfx_vol = rel
                    if self.hover_snd:
                        self.hover_snd.set_volume(rel)
            return

    def render(self):
        if not self.is_open:
            return
        W, H = self.display.get_size()

        # Blur + darken
        snap  = self.display.copy()
        small = pygame.transform.smoothscale(snap, (W//10, H//10))
        blur  = pygame.transform.smoothscale(small, (W, H))
        self.display.blit(blur, (0,0))
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        self.display.blit(ov, (0,0))

        # Panel
        panel = pygame.Surface((self.pw, self.ph), pygame.SRCALPHA)
        panel.fill((30,30,30,230))
        rect = panel.get_rect(center=(W//2, H//2))
        self.display.blit(panel, rect)

        def dc(c, f, x, y, col):
            for dx in range(-self.border, self.border+1):
                for dy in range(-self.border, self.border+1):
                    if dx == 0 and dy == 0: continue
                    s = f.render(c, True, (0,0,0)).convert_alpha()
                    self.display.blit(s, (x+dx, y+dy))
            s = f.render(c, True, col).convert_alpha()
            self.display.blit(s, (x, y))
            return f.size(c)[0]

        # Title
        title = "Menu"
        ft = self.fonts['title']
        tw = sum(ft.size(c)[0] for c in title)
        x = W//2 - tw//2
        y = rect.top + int(self.ph * 0.13) - ft.get_height()//2
        for c in title:
            x += dc(c, ft, x, y, (255,255,255))

        fi = self.fonts['item']
        box_w = self.pw - int(200 * self.scale)
        bx = rect.left + (self.pw - box_w)//2
        ih = fi.get_height() + int(8 * self.scale)
        margin_y = int(140 * self.scale)
        fps_gap = int(40 * self.scale)
        res_y = rect.top + margin_y
        fps_y = res_y + ih + fps_gap
        fs_y  = fps_y + ih + fps_gap

        # Graphic submenu rendering
        if self.in_graphic:
            if not self.open_fps:
                lbl = "Resolution"
                lx = W//2 - fi.size('0')[0]*len(lbl)//2
                ly = res_y - int(40 * self.scale)
                for c in lbl:
                    lx += dc(c, fi, lx, ly, (255,255,255))
                pygame.draw.rect(self.display, (100,100,100), (bx, res_y, box_w, ih))
                tx, ty = bx + int(10 * self.scale), res_y + int(4 * self.scale)
                for c in self.res_strs[self.sel_res]:
                    tx += dc(c, fi, tx, ty, (255,255,255))
                pygame.draw.polygon(self.display, (255,255,255), [
                    (bx + box_w - int(20 * self.scale), res_y + ih//2 - int(5 * self.scale)),
                    (bx + box_w - int(10 * self.scale), res_y + ih//2 - int(5 * self.scale)),
                    (bx + box_w - int(15 * self.scale), res_y + ih//2 + int(5 * self.scale))
                ])
            if not self.open_res:
                lbl = "FPS"
                lx = W//2 - fi.size('0')[0]*len(lbl)//2
                ly = fps_y - int(40 * self.scale)
                for c in lbl:
                    lx += dc(c, fi, lx, ly, (255,255,255))
                pygame.draw.rect(self.display, (100,100,100), (bx, fps_y, box_w, ih))
                tx, ty = bx + int(10 * self.scale), fps_y + int(4 * self.scale)
                for c in str(self.fps_list[self.sel_fps]):
                    tx += dc(c, fi, tx, ty, (255,255,255))
                pygame.draw.polygon(self.display, (255,255,255), [
                    (bx + box_w - int(20 * self.scale), fps_y + ih//2 - int(5 * self.scale)),
                    (bx + box_w - int(10 * self.scale), fps_y + ih//2 - int(5 * self.scale)),
                    (bx + box_w - int(15 * self.scale), fps_y + ih//2 + int(5 * self.scale))
                ])
            if not (self.open_res or self.open_fps):
                lbl = "Fullscreen"
                lx = W//2 - fi.size('0')[0]*len(lbl)//2
                ly = fs_y - int(40 * self.scale)
                for c in lbl:
                    lx += dc(c, fi, lx, ly, (255,255,255))
                pygame.draw.rect(self.display, (100,100,100), (bx, fs_y, box_w, ih))
                state = "On" if self.fullscreen else "Off"
                tx, ty = bx + int(10 * self.scale), fs_y + int(4 * self.scale)
                for c in state:
                    tx += dc(c, fi, tx, ty, (255,255,255))

            if self.open_res:
                for i, opt in enumerate(self.res_strs):
                    oy = res_y + ih * (i+1)
                    pygame.draw.rect(self.display, (50,50,50), (bx, oy, box_w, ih))
                    tx, ty = bx + int(10 * self.scale), oy + int(4 * self.scale)
                    for c in opt:
                        tx += dc(c, fi, tx, ty, (255,255,255))

            if self.open_fps:
                for i, opt in enumerate(self.fps_list):
                    oy = fps_y + ih * (i+1)
                    pygame.draw.rect(self.display, (50,50,50), (bx, oy, box_w, ih))
                    tx, ty = bx + int(10 * self.scale), oy + int(4 * self.scale)
                    for c in str(opt):
                        tx += dc(c, fi, tx, ty, (255,255,255))

            tip = fi.render("Press ESC to go back", True, (180,180,180))
            self.display.blit(tip, ((W - tip.get_width())//2, rect.bottom - int(40 * self.scale)))
            return

        # Sound submenu rendering
        if self.in_sound:
            my_line = rect.top + self.ph//2 - int(50 * self.scale)
            sy_line = my_line + int(100 * self.scale)
            kr = int(10 * self.scale)
            pygame.draw.rect(self.display, (100,100,100), (bx, my_line - int(5 * self.scale), box_w, int(10 * self.scale)))
            pygame.draw.rect(self.display, (100,100,100), (bx, sy_line - int(5 * self.scale), box_w, int(10 * self.scale)))
            lblm = "Music"
            lx, ly = bx, my_line - int(40 * self.scale)
            for c in lblm:
                lx += dc(c, fi, lx, ly, (255,255,255))
            lbls = "Sounds"
            lx2, ly2 = bx, sy_line - int(40 * self.scale)
            for c in lbls:
                lx2 += dc(c, fi, lx2, ly2, (255,255,255))
            mxk = bx + int(box_w * self.music_vol)
            sxk = bx + int(box_w * self.sfx_vol)
            pygame.draw.circle(self.display, (200,200,0) if self.dragging=='music' else (255,255,255), (mxk, my_line), kr)
            pygame.draw.circle(self.display, (200,200,0) if self.dragging=='sfx' else (255,255,255), (sxk, sy_line), kr)
            tip = fi.render("Press ESC to go back", True, (180,180,180))
            self.display.blit(tip, ((W - tip.get_width())//2, rect.bottom - int(40 * self.scale)))
            return

        # Main menu rendering
        mx, my = pygame.mouse.get_pos()
        new_hover = None
        item_gap = int(50 * self.scale)
        for idx, text in enumerate(self.items):
            tw = sum(fi.size(c)[0] for c in text)
            rx = W//2 - tw//2
            ry = rect.top + margin_y + idx * item_gap - fi.get_height()//2
            if pygame.Rect(rx, ry, tw, fi.get_height()).collidepoint(mx, my):
                new_hover = idx
                break
        if new_hover is not None and new_hover != self.hover and self.hover_snd:
            self.hover_snd.play()
        self.hover = new_hover

        for idx, text in enumerate(self.items):
            color = (255,255,0) if idx == self.hover else (255,255,255)
            x = W//2 - sum(fi.size(c)[0] for c in text)//2
            y = rect.top + margin_y + idx * item_gap - fi.get_height()//2
            for c in text:
                x += dc(c, fi, x, y, color)
