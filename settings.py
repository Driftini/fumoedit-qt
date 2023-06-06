import fumoedit
import json
from os import path

SETTINGS_FILE = "feqt_settings.json"

# Default application-wide settings
settings = {
    "wordwrap": False,
    "fontsize_body": 9,
    "fontsize_preview": 9,
    "site_path": "."
}

def load_settings():
    if path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            settings = json.load(f.read())
    else:
        save_settings()

def save_settings():
    with open(SETTINGS_FILE, mode="w", encoding="utf-8") as f:
        f.write(json.dump(settings))

def set_site_path(newpath):
    settings["site_path"] = newpath
    fumoedit.site_root = newpath
    
    
