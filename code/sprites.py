import pygame
from settings import *
from resource_manager import *


class WorldSprite(pygame.sprite.Sprite):
    def __init__(self, pos, image_path, groups, ground=False):
        super().__init__(groups)
        self.image = ResourceManager.load_image(image_path)
        self.rect = self.image.get_rect()
        if ground:
            self.ground = True


"""""
class Item(pygame.sprite.Sprite):
    def __init__(self, pos, image_path, groups):
        super().__init__(groups)
        self.image = ResourceManager.load_image(image_path)
        self.rect = self.image.get_rect(topleft=pos)
"""""
