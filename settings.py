import pickle

SETTINGS_FILE = "feqt_settings.pickle"

# Default application-wide settings
settings = {
    "wrap_body": True,
    "wrap_preview": True,
    "fontsize_body": 8,
    "fontsize_preview": 9,
    "site_path": "/"
}


def load_settings():
    try:
        with open(SETTINGS_FILE, mode="br") as f:
            settings.update(pickle.load(f))
    except (OSError):
        # If file doesn't exist, create one with default settings
        save_settings()


def save_settings():
    with open(SETTINGS_FILE, mode="bw") as f:
        pickle.dump(settings, f)


def set_site_path(newpath):
    settings["site_path"] = newpath
