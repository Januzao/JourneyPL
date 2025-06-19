import pygame
from pathlib import Path
from settings import PARENT_DIR

class MusicManager:
    def __init__(self, volume: float = 0.5):
        pygame.mixer.music.set_volume(volume)

    def load(self, filename: str):
        music_path = Path(PARENT_DIR) / 'data' / 'audio' / filename
        pygame.mixer.music.load(str(music_path))


    def play(self, loops: int = -1):
            pygame.mixer.music.play(loops=loops)


    def stop(self):
        pygame.mixer.music.stop()
