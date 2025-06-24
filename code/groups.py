# groups.py

import pygame

class CameraGroup(pygame.sprite.Group):
    """
    Sprite group with automatic camera centering on a target sprite,
    plus optional parallax layers.
    """
    def __init__(self):
        super().__init__()
        # Surface on which to draw (updated dynamically)
        self.display_surface = pygame.display.get_surface()
        # Camera offset vector
        self.offset = pygame.math.Vector2()
        # The sprite to follow
        self.target = None
        # Background layers for parallax: list of (surface, speed)
        self.parallax_layers = []

    def set_target(self, sprite: pygame.sprite.Sprite) -> None:
        """Set the sprite that the camera should follow."""
        self.target = sprite

    def add_parallax_layer(self, surface: pygame.Surface, speed: float) -> None:
        """Add a parallax background layer."""
        self.parallax_layers.append((surface, speed))

    def _calculate_offset(self) -> None:
        """
        Update self.offset so that the target is centered on screen,
        regardless of resolution.
        """
        if not self.target:
            return
        # Get current screen size
        screen_w, screen_h = self.display_surface.get_size()
        half_w, half_h = screen_w // 2, screen_h // 2
        # Center target
        self.offset.x = -(self.target.rect.centerx - half_w)
        self.offset.y = -(self.target.rect.centery - half_h)

    def draw(self) -> None:
        """
        Draw parallax layers and sprites, centering camera on target.
        Sprites with attribute ground=True are drawn before others.
        """
        # Refresh display surface in case of resize/fullscreen
        self.display_surface = pygame.display.get_surface()
        # Update camera offset
        self._calculate_offset()

        # Draw parallax background layers
        for bg_surface, speed in self.parallax_layers:
            parallax_offset = self.offset * speed
            self.display_surface.blit(bg_surface, parallax_offset)

        # Separate sprites by ground flag
        ground_sprites = [s for s in self if getattr(s, 'ground', False)]
        object_sprites = [s for s in self if not getattr(s, 'ground', False)]

        # Draw ground, then objects sorted by y-position for proper overlap
        for sprite_group in (ground_sprites, object_sprites):
            for sprite in sorted(sprite_group, key=lambda spr: spr.rect.centery):
                pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, pos)
