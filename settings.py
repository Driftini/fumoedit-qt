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
    "site_path": path.normpath("/")
}


def load_settings():
    try:
        with open(SETTINGS_FILE, mode="br") as f:
            settings.update(pickle.load(f))

            fumoedit.site_path = settings["site_path"]
    except (OSError):
        # If file doesn't exist, create one with default settings
        save_settings()


def save_settings():
    with open(SETTINGS_FILE, mode="bw") as f:
        pickle.dump(settings, f)


def set_site_path(newpath):
    settings["site_path"] = path.normpath(newpath)
