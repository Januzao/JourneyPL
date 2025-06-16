import pygame
from settings import *
from resource_manager import *


# class WorldSprite(pygame.sprite.Sprite):
#     def __init__(self, pos, image_path, groups, ground=False):
#         super().__init__(groups)
#         self.image = ResourceManager.load_image(image_path)
#         self.rect = self.image.get_rect()
#         if ground:
#             self.ground = True

class WorldSprite(pygame.sprite.Sprite):
    def __init__(self, pos, image_source, groups, ground=False):
        super().__init__(groups)
        # Якщо передано вже Surface (наприклад, із TMX), використовуємо його напряму
        if isinstance(image_source, pygame.Surface):
            self.image = image_source
        else:
            # Інакше підвантажуємо за шляхом через ResourceManager
            self.image = ResourceManager.load_image(image_source)
        self.rect = self.image.get_rect(topleft=pos)
        if ground:
            self.ground = True
