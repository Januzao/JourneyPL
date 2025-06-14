from pathlib import Path
import pygame
from pytmx import pytmx
from settings import PARENT_DIR
from typing import Dict, Union
from pytmx.util_pygame import load_pygame
class ResourceManager:
    # Словник для кешування завантажених Surface
    _images: Dict[Path, pygame.Surface] = {}
    # Словник для кешування TMX-карт
    _tmx_data: Dict[Path, pytmx.TiledMap] = {}

    @classmethod
    def load_image(cls, rel_path: Union[str, Path]) -> pygame.Surface:
        """
        1. Приймає шлях до зображення, відносно кореня проєкту.
        2. Якщо зображення ще не завантажено, завантажує через pygame.image.load, виконує convert_alpha().
        3. Зберігає Surface у кеш (_images) за ключем Path.
        4. Повертає Surface із кешу.
        """
        path = PARENT_DIR / rel_path
        path = Path(path)
        if path not in cls._images:
            cls._images[path] = pygame.image.load(path).convert_alpha()
        return cls._images[path]

    @classmethod
    def load_tmx(cls, rel_path: Union[str, Path]) -> pytmx.TiledMap:
        """
        1. Завантажує та кешує TMX-картку через pytmx.util_pygame.load_pygame.
        2. Повторний виклик повертає вже завантажену копію.
        """
        path = PARENT_DIR / rel_path
        path = Path(path)
        if path not in cls._tmx_data:
            cls._tmx_data[path] = load_pygame(path)
        return cls._tmx_data[path]