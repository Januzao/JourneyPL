# config.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / 'config.json'

DEFAULT_CONFIG = {
    "resolution": [1280, 720],
    "fps": 60,
    "fullscreen": False
}

def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, 'r') as f:
            cfg = json.load(f)
        return {
            "resolution": cfg.get("resolution", DEFAULT_CONFIG["resolution"]),
            "fps": cfg.get("fps", DEFAULT_CONFIG["fps"]),
            "fullscreen": cfg.get("fullscreen", DEFAULT_CONFIG["fullscreen"])
        }
    except Exception:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=4)
