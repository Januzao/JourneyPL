from pathlib import Path

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

# tile size in used to precision
TILE_SIZE = 64
FPS = 60

ANIMATION_SPEED = 5
PICKUP_RADIUS = 100

# Paths
# Parent path
PARENT_DIR = Path(__file__).parent.parent
# Tile sprites
SPRITES_DIR = PARENT_DIR / 'data' / 'graphics' / 'sprites'
# Sticker sprites
STICKERS_DIR = PARENT_DIR / 'data' / 'graphics' / 'stickers'
# Objects folder
OBJECTS_DIR = PARENT_DIR / 'data' / 'graphics' / 'objects'
# UI elements
UI_DIR = PARENT_DIR / 'data' / 'graphics' / 'ui'
# Player sprites and animations
PLAYER_DIR = PARENT_DIR / 'images' / 'player'
# Maps and tilesets
MAPS_DIR = PARENT_DIR / 'data' / 'maps'
TILESETS_DIR = PARENT_DIR / 'data' / 'tilesets'
# Audio, music.
AUDIO_DIR = PARENT_DIR / 'data' / 'audio'
