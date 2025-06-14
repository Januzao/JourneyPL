from pathlib import Path
from typing import List
from pygame import Surface
from resource_manager import ResourceManager
from settings import PARENT_DIR


# 1) Збір шляхів до кадрів анімації
def collect_image_paths(state: str) -> List[Path]:
    base = PARENT_DIR / 'images' / 'player' / state
    # повертаємо відсортований список .png-файлів
    return sorted(p for p in base.iterdir() if p.suffix == '.png')


# 2) Завантаження кадрів у пам'ять
def load_images_from_paths(paths: List[Path]) -> List[Surface]:
    frames: List[Surface] = []
    for path in paths:
        # використовуємо ResourceManager для кешування
        rel = path.relative_to(PARENT_DIR)
        img = ResourceManager.load_image(rel)
        frames.append(img)
    return frames
