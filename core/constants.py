from enum import Enum
from pathlib import Path

# Enum for database column names
# Outlines database id for queries, and their child query, e.g. Genres --> Fetch song_titles for each genre
ROOT = Path(__file__).resolve().parent.parent


class SongQueryType(Enum):
    GENRE = {
        "db_id": "song_genre",
        "db_child": "song_title",
    }
    ARTIST = {
        "db_id": "song_artist",
        "db_child": "song_album",
    }
    ALBUM = {
        "db_id": "song_album",
        "db_child": "song_title",
    }
    TITLE = {
        "db_id": "song_title",
        "db_child": "song_title",
    }

    ALL_GENRE = {
        "db_id": "song_genre",
        "db_child": "song_genre",
    }
    ALL_ARTIST = {
        "db_id": "song_artist",
        "db_child": "song_artist",
    }
    ALL_ALBUM = {
        "db_id": "song_album",
        "db_child": "song_album",
    }

    @classmethod
    def from_db_id(cls, target_db_id):
        for member in cls:
            if member.value.get("db_id") == target_db_id:
                return member
        return None


# CHECKS WHAT BUTTON DOES, add values later if necessary
class ButtonCommands(Enum):
    BATCH = ""
    SPECIFIC = ""
    SONG = ""


class HomeScreenButton(Enum):
    PLAYBACK = ""
    LIBRARY = [  # MAKE IT SO BCMD TELLS WHAT THE BUTTON IS, IF ITS LOOKING FOR ALL (BATCH) IN THE CATEGORY OR IF SPECIFIC
        {
            "text": "Shuffle",
            "item_id": 0,
            "btype": None,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
        {
            "text": "Songs",
            "item_id": 1,
            "btype": SongQueryType.TITLE,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
        {
            "text": "Artists",
            "item_id": 2,
            "btype": SongQueryType.ALL_ARTIST,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
        {
            "text": "Albums",
            "item_id": 3,
            "btype": SongQueryType.ALL_ALBUM,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
        {
            "text": "Playlists",
            "item_id": 4,
            "btype": None,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
        {
            "text": "Genres",
            "item_id": 5,
            "btype": SongQueryType.ALL_GENRE,
            "has_params": False,
            "selected": False,
            "song_id": None,
        },
    ]
    SPOTIFY = ""
    SETTINGS = ""


class PlaylistQueryType:
    pass
