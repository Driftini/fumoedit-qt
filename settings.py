from os import path
import pickle
import fumoedit

SETTINGS_FILE = "feqt_settings.pickle"

# Default application-wide settings
settings = {
    "wrap_body": True,
    "wrap_preview": True,
    "fontsize_body": 8,
    "fontsize_preview": 9,
    "site_path": path.normpath("/"),
    "tag_priority": []
}


def load_settings():
    try:
        with open(SETTINGS_FILE, mode="br") as f:
            settings.update(pickle.load(f))

            sync_fumoedit()
    except (OSError):
        # If file doesn't exist, create one with default settings
        save_settings()


def save_settings():
    with open(SETTINGS_FILE, mode="bw") as f:
        pickle.dump(settings, f)
    
    sync_fumoedit()


def set_site_path(newpath):
    settings["site_path"] = path.normpath(newpath)


def set_tag_priority(newtp):
    settings["tag_priority"] = list(dict.fromkeys(newtp)).copy()


def sync_fumoedit():
    # Synchronize shared settings between FumoEdit-QT and fumoedit
    fumoedit.site_path = settings["site_path"]
    fumoedit.tag_priority = settings["tag_priority"].copy()