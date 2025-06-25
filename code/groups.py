"""Camera group with dynamic window support.

Fixes issue where camera offset is wrong when the game runs in a
resolution different from the compile‑time constants declared in
``settings.py`` (e.g. 1920×720).  The group now recalculates half
window sizes every frame so that the target (usually the player)
remains centred regardless of the current display size or when the
window is resized/fullscreen toggled at runtime.
"""

import pygame

__all__ = ["CameraGroup"]


class CameraGroup(pygame.sprite.Group):
    """A sprite group that behaves like a camera following a target.

    *   Parallax background layers can be added so that their parallax
        speed factor is applied automatically.
    *   The group keeps the *target* sprite in the centre of the window
        by translating every blit by ``self.offset``.
    *   Window size is **queried every frame**, so changing resolution or
        toggling fullscreen in‑game works without glitches.
    """

    def __init__(self) -> None:
        super().__init__()

        # The surface we actually draw to.  We refresh this reference in
        # :meth:`draw` so that it follows the latest call to
        # ``pygame.display.set_mode``.
        self.display_surface: pygame.Surface = pygame.display.get_surface()

        # Translation that must be applied to every world‑space position
        # so that the camera target appears centred on screen.
        self.offset = pygame.math.Vector2()

        # These will be **re‑evaluated each frame**; they are initialised
        # here merely so that the attributes exist.
        self.half_w: int = self.display_surface.get_width() // 2
        self.half_h: int = self.display_surface.get_height() // 2

        # Sprite we are tracking (usually the player).
        self.target: pygame.sprite.Sprite | None = None

        # Optional parallax background layers: list of (surface, speed).
        self.parallax_layers: list[tuple[pygame.Surface, float]] = []

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def set_target(self, sprite: pygame.sprite.Sprite) -> None:  # noqa: D401
        """Tell the camera which *sprite* to keep in view."""
        self.target = sprite

    def add_parallax_layer(self, surface: pygame.Surface, speed: float) -> None:
        """Register *surface* as a parallax layer with the given *speed*.

        ``speed`` is the fraction of camera movement applied to the layer.
        ``1.0`` means the layer is static to the camera (like the game
        world), ``0.5`` means it moves at half speed and therefore looks
        twice as far away, etc.
        """
        self.parallax_layers.append((surface, speed))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_window_half_sizes(self) -> None:
        """Refresh ``self.half_w`` and ``self.half_h`` to current window."""
        self.half_w = self.display_surface.get_width() // 2
        self.half_h = self.display_surface.get_height() // 2

    def _calculate_offset(self) -> None:
        """Recompute ``self.offset`` so that *target* is centred."""
        if not self.target:
            return  # Nothing to follow yet

        # Ensure half‑sizes are in sync with possible runtime resizes.
        self._update_window_half_sizes()

        self.offset.x = -(self.target.rect.centerx - self.half_w)
        self.offset.y = -(self.target.rect.centery - self.half_h)

    # ------------------------------------------------------------------
    # Main draw routine
    # ------------------------------------------------------------------

    def draw(self) -> None:  # type: ignore[override]
        """Draw parallax layers first, then sprites in depth order."""

        # Keep a fresh reference to whatever surface the game is currently
        # using (fullscreen toggle, res change, etc.).
        self.display_surface = pygame.display.get_surface()

        # Compute the camera translation to centre the target.
        self._calculate_offset()

        # 1.  Draw parallax backgrounds.
        for bg_surface, speed in self.parallax_layers:
            parallax_offset = self.offset * speed
            self.display_surface.blit(bg_surface, parallax_offset)

        # 2.  Draw sprites.  We render those marked ``ground=True`` first
        #     so that things like grass stay under the player.
        ground_sprites = [s for s in self if getattr(s, "ground", False)]
        object_sprites = [s for s in self if not getattr(s, "ground", False)]

        for group in (ground_sprites, object_sprites):
            # Sort by y so that objects further down screen overlap the
            # ones behind (simple painter's algorithm).
            for sprite in sorted(group, key=lambda spr: spr.rect.centery):
                pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, pos)
