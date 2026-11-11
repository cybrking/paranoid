"""User profiles."""

from . import net

MAX_AVATAR_BYTES = 2 * 1024 * 1024


class Store:
    def __init__(self):
        self.profiles = {}  # user_id -> {"name": str, "avatar": bytes | None}

    def add(self, user_id, name):
        self.profiles[user_id] = {"name": name, "avatar": None}


def rename(store, user_id, name):
    if not name or len(name) > 80:
        raise ValueError("name must be 1 to 80 characters")
    store.profiles[user_id]["name"] = name


def set_avatar_from_url(store, user_id, url):
    """Fetch the image at url and store it as the user's avatar (PROF-12)."""
    data = net.fetch(url)
    if len(data) > MAX_AVATAR_BYTES:
        raise ValueError("avatar is larger than 2 MB")
    store.profiles[user_id]["avatar"] = data
