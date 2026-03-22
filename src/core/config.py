import json
import os

DEFAULT_SETTINGS = {
    "theme": "dark",
    "color_theme": "blue",
    "compression_quality": 75,
    "image_dpi": 150,
    "default_output_dir": "",
    "recent_files": [],
    "max_recent_files": 10,
    "signature_color": "#000000",
    "signature_pen_size": 2,
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "settings.json")


def load_settings():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def add_recent_file(settings, filepath):
    recent = settings.get("recent_files", [])
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    settings["recent_files"] = recent[: settings.get("max_recent_files", 10)]
    save_settings(settings)
