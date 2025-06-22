# menu.py

import pygame
from pathlib import Path
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, PARENT_DIR


class Menu:
    def __init__(self, display: pygame.Surface, font_choices: dict[str, str], border_thickness: int = 2):
        self.display = display
        self.is_open = False
        self.in_sound = False
        self.in_graphic = False
        self.border = border_thickness
        self.hover = None

        # --- Sound settings ---
        self.music_vol = 0.5
        self.sfx_vol = 0.5
        self.dragging = None

        # --- Graphic settings ---
        pygame.font.init()
        modes = pygame.display.list_modes()
        candidates = [(1280, 720), (1920, 1080), (2560, 1440)]
        self.res_list = [r for r in candidates if r in modes]
        self.res_strs = [f"{w}x{h}" for w, h in self.res_list]
        self.fps_list = [30, 60, 90, 120, 144]
        self.sel_res = 0
        self.sel_fps = 1  # default 60
        self.open_res = False
        self.open_fps = False

        # fonts
        self.fonts: dict[str, pygame.font.Font] = {}
        for k, p in font_choices.items():
            sz = 72 if k == 'title' else 36
            self.fonts[k] = pygame.font.Font(p, sz) if p else pygame.font.SysFont(None, sz)

        # main items
        self.items = ["Graphic Settings", "Sound Settings", "Achievements", "Exit"]
        # hover sound
        hover_path = Path(PARENT_DIR) / 'data' / 'audio' / 'sounds' / 'hover.mp3'
        try:
            self.hover_snd = pygame.mixer.Sound(str(hover_path))
            self.hover_snd.set_volume(self.sfx_vol)
        except:
            self.hover_snd = None
        pygame.mixer.music.set_volume(self.music_vol)

    def toggle(self):
        self.is_open = not self.is_open
        self.in_sound = self.in_graphic = False
        self.open_res = self.open_fps = False
        self.hover = None

    def handle_event(self, event):
        if not self.is_open: return

        # click on main menu
        if event.type == pygame.MOUSEBUTTONDOWN and not (self.in_sound or self.in_graphic):
            if self.hover == 0:
                self.in_graphic = True;
                self.open_res = self.open_fps = False;
                return
            if self.hover == 1:
                self.in_sound = True;
                self.dragging = None;
                return

        # graphic submenu
        if self.in_graphic:
            W, H = self.display.get_size()
            pw, ph = 600, 450
            rect = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
            box_w = pw - 200
            box_x = rect.left + (pw - box_w) // 2
            fi = self.fonts['item']
            ih = fi.get_height() + 8
            res_y = rect.top + 140
            fps_y = res_y + ih + 40

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.in_graphic = self.open_res = self.open_fps = False;
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # FPS box
                rb = pygame.Rect(box_x, fps_y, box_w, ih)
                if rb.collidepoint(mx, my):
                    self.open_fps = not self.open_fps;
                    self.open_res = False;
                    return
                if self.open_fps:
                    for i, _ in enumerate(self.fps_list):
                        ob = pygame.Rect(box_x, fps_y + ih * (i + 1), box_w, ih)
                        if ob.collidepoint(mx, my):
                            self.sel_fps = i;
                            self.open_fps = False;
                            return
                # RES box
                sb = pygame.Rect(box_x, res_y, box_w, ih)
                if sb.collidepoint(mx, my):
                    self.open_res = not self.open_res;
                    self.open_fps = False;
                    return
                if self.open_res:
                    for i, _ in enumerate(self.res_strs):
                        ob = pygame.Rect(box_x, res_y + ih * (i + 1), box_w, ih)
                        if ob.collidepoint(mx, my):
                            self.sel_res = i;
                            self.open_res = False;
                            return
            return

        # sound submenu
        if self.in_sound:
            W, H = self.display.get_size()
            pw, ph = 600, 450
            rect = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
            box_w = pw - 200
            box_x = rect.left + (pw - box_w) // 2
            my = rect.top + ph // 2 - 50
            sy = my + 100
            kr = 10

            mxk = box_x + int(box_w * self.music_vol)
            sxk = box_x + int(box_w * self.sfx_vol)

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if (x - mxk) ** 2 + (y - my) ** 2 <= kr ** 2: self.dragging = 'music'
                if (x - sxk) ** 2 + (y - sy) ** 2 <= kr ** 2: self.dragging = 'sfx'

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = None

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                x, _ = event.pos
                rel = max(0, min(x - box_x, box_w)) / box_w
                if self.dragging == 'music':
                    self.music_vol = rel;
                    pygame.mixer.music.set_volume(rel)
                else:
                    self.sfx_vol = rel
                    if self.hover_snd: self.hover_snd.set_volume(rel)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.in_sound = self.dragging = None
            return

    def render(self):
        if not self.is_open: return
        W, H = self.display.get_size()
        # blur & darken
        snap = self.display.copy()
        small = pygame.transform.smoothscale(snap, (W // 10, H // 10))
        blur = pygame.transform.smoothscale(small, (W, H))
        self.display.blit(blur, (0, 0))
        ov = pygame.Surface((W, H), pygame.SRCALPHA);
        ov.fill((0, 0, 0, 180));
        self.display.blit(ov, (0, 0))

        # panel
        pw, ph = 600, 450
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA);
        panel.fill((30, 30, 30, 230))
        rect = panel.get_rect(center=(W // 2, H // 2));
        self.display.blit(panel, rect)

        # helper
        def dc(c, f, x, y, col):
            for dx in range(-self.border, self.border + 1):
                for dy in range(-self.border, self.border + 1):
                    if dx == 0 and dy == 0: continue
                    s = f.render(c, True, (0, 0, 0)).convert_alpha();
                    self.display.blit(s, (x + dx, y + dy))
            s = f.render(c, True, col).convert_alpha();
            self.display.blit(s, (x, y))
            return f.size(c)[0]

        # title
        title = "Menu";
        ft = self.fonts['title']
        tw = sum(ft.size(c)[0] for c in title)
        x = W // 2 - tw // 2;
        y = rect.top + 60 - ft.get_height() // 2
        for c in title: x += dc(c, ft, x, y, (255, 255, 255))

        # graphic
        if self.in_graphic:
            fi = self.fonts['item']
            box_w = pw - 200;
            bx = rect.left + (pw - box_w) // 2;
            ih = fi.get_height() + 8
            ry = rect.top + 140;
            fy = ry + ih + 40
            # FPS (on top)
            lbl = "FPS";
            lx = W // 2 - fi.size('0')[0] * len(lbl) // 2;
            ly = fy - 40
            for c in lbl: lx += dc(c, fi, lx, ly, (255, 255, 255))
            pygame.draw.rect(self.display, (100, 100, 100), (bx, fy, box_w, ih))
            tx, ty = bx + 10, fy + 4
            for c in str(self.fps_list[self.sel_fps]): tx += dc(c, fi, tx, ty, (255, 255, 255))
            pygame.draw.polygon(self.display, (255, 255, 255), [
                (bx + box_w - 20, fy + ih // 2 - 5), (bx + box_w - 10, fy + ih // 2 - 5),
                (bx + box_w - 15, fy + ih // 2 + 5)
            ])
            if self.open_fps:
                for i, opt in enumerate(self.fps_list):
                    oy = fy + ih * (i + 1)
                    pygame.draw.rect(self.display, (50, 50, 50), (bx, oy, box_w, ih))
                    tx2, ty2 = bx + 10, oy + 4
                    for c in str(opt): tx2 += dc(c, fi, tx2, ty2, (255, 255, 255))
            # Res (below)
            lbl2 = "Resolution";
            lx2 = W // 2 - fi.size('0')[0] * len(lbl2) // 2;
            ly2 = ry - 40
            for c in lbl2: lx2 += dc(c, fi, lx2, ly2, (255, 255, 255))
            pygame.draw.rect(self.display, (100, 100, 100), (bx, ry, box_w, ih))
            tx3, ty3 = bx + 10, ry + 4
            for c in self.res_strs[self.sel_res]: tx3 += dc(c, fi, tx3, ty3, (255, 255, 255))
            pygame.draw.polygon(self.display, (255, 255, 255), [
                (bx + box_w - 20, ry + ih // 2 - 5), (bx + box_w - 10, ry + ih // 2 - 5),
                (bx + box_w - 15, ry + ih // 2 + 5)
            ])
            if self.open_res:
                for i, opt in enumerate(self.res_strs):
                    oy = ry + ih * (i + 1)
                    pygame.draw.rect(self.display, (50, 50, 50), (bx, oy, box_w, ih))
                    tx4, ty4 = bx + 10, oy + 4
                    for c in opt: tx4 += dc(c, fi, tx4, ty4, (255, 255, 255))
            # back tip
            tip = self.fonts['item'].render("Press ESC to go back", True, (180, 180, 180))
            self.display.blit(tip, (rect.centerx - tip.get_width() // 2, rect.bottom - 40))
            return

        # sound
        if self.in_sound:
            fi = self.fonts['item']
            box_w = pw - 200;
            bx = rect.left + (pw - box_w) // 2
            my = rect.top + ph // 2 - 50;
            sy = my + 100;
            kr = 10
            # labels
            lblm = "Music";
            lx = bx;
            ly = my - 40
            for c in lblm: lx += dc(c, fi, lx, ly, (255, 255, 255))
            lbls = "Sounds";
            lx2 = bx;
            ly2 = sy - 40
            for c in lbls: lx2 += dc(c, fi, lx2, ly2, (255, 255, 255))
            # bars
            pygame.draw.rect(self.display, (100, 100, 100), (bx, my - 5, box_w, 10))
            pygame.draw.rect(self.display, (100, 100, 100), (bx, sy - 5, box_w, 10))
            # knobs
            mxk = bx + int(box_w * self.music_vol);
            sxk = bx + int(box_w * self.sfx_vol)
            pygame.draw.circle(self.display, (200, 200, 0) if self.dragging == 'music' else (255, 255, 255), (mxk, my),
                               kr)
            pygame.draw.circle(self.display, (200, 200, 0) if self.dragging == 'sfx' else (255, 255, 255), (sxk, sy),
                               kr)
            tip = self.fonts['item'].render("Press ESC to go back", True, (180, 180, 180))
            self.display.blit(tip, (rect.centerx - tip.get_width() // 2, rect.bottom - 40))
            return

        # main menu
        mx, my = pygame.mouse.get_pos()
        new = None;
        fi = self.fonts['item'];
        sy = rect.top + 140
        for i, t in enumerate(self.items):
            tw = sum(fi.size(c)[0] for c in t)
            rx = W // 2 - tw // 2;
            ry = sy + i * 50 - fi.get_height() // 2
            if pygame.Rect(rx, ry, tw, fi.get_height()).collidepoint(mx, my): new = i; break
        if new is not None and new != self.hover:
            if self.hover_snd: self.hover_snd.play()
        self.hover = new
        for i, t in enumerate(self.items):
            col = (255, 255, 0) if i == self.hover else (255, 255, 255)
            x = W // 2 - sum(self.fonts['item'].size(c)[0] for c in t) // 2
            y = sy + i * 50 - fi.get_height() // 2
            for c in t: x += dc(c, fi, x, y, col)
