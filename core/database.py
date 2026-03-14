import sqlite3
import core.constants as const
from pathlib import Path
from mutagen.flac import FLAC
from mutagen.mp3 import MP3

# DATABASE TABLES
song_table = """
CREATE TABLE IF NOT EXISTS song (
song_id INTEGER PRIMARY KEY AUTOINCREMENT,
song_genre TEXT,
song_artist TEXT,
song_album TEXT,
song_title TEXT,
song_duration INTEGER,
song_track TEXT,
song_dir TEXT UNIQUE
);
"""

playlist_table = """
CREATE TABLE IF NOT EXISTS playlist (
playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
playlist_name TEXT
);
"""

playlist_song_table = """
CREATE TABLE IF NOT EXISTS playlist_song (
playlist_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
playlist_id INTEGER,
song_id INTEGER,
playlist_position INTEGER,
UNIQUE (playlist_id, playlist_position),
FOREIGN KEY (playlist_id) REFERENCES playlist(playlist_id)
);
"""

settings_table = """
CREATE TABLE IF NOT EXISTS settings (
settings_id INTEGER PRIMARY KEY AUTOINCREMENT,
settings_volume INTEGER DEFAULT 50,
settings_shuffle BOOLEAN DEFAULT FALSE
);
"""

user_table = """
CREATE TABLE IF NOT EXISTS user (
user_id INTEGER PRIMARY KEY AUTOINCREMENT,
song_id INTEGER DEFAULT NULL,
settings_id INTEGER DEFAULT 0,
playlist_id INTEGER DEFAULT NULL,
FOREIGN KEY (song_id) REFERENCES song(song_id) ON DELETE SET NULL,
FOREIGN KEY (settings_id) REFERENCES settings(settings_id) ON DELETE SET DEFAULT,
FOREIGN KEY (playlist_id) REFERENCES playlist(playlist_id) ON DELETE SET NULL
);
"""

# INITIAL DATABASE INSERTS
playlist_insert = """
INSERT OR IGNORE INTO playlist VALUES (0, 'queue')
"""
settings_insert = """
INSERT OR IGNORE INTO settings (settings_id) VALUES (0)
"""
user_insert = """
INSERT OR IGNORE INTO user (user_id) VALUES (0)
"""

# Default table states
tables = {song_table, playlist_table, playlist_song_table, settings_table, user_table}
inserts = {playlist_insert, settings_insert, user_insert}


# Handles current working memory, and is a medium for interaction with db
class Database:
    def __init__(self, USER_ID):
        self.current_song = None
        self.current_queue = None
        self.volume = None
        self.connection = sqlite3.connect(
            "piPod.db", check_same_thread=False, timeout=10
        )  # Allows threading, and will wait up to 10 seconds before erroring if can't access
        self.cursor = self.connection.cursor()
        self.ROOT = const.ROOT
        self.USER_ID = USER_ID
        self.LIBRARY = self.ROOT / "MusicLibrary"

        found_user = False

        # If no users can be found, will run initial startup
        try:
            self.cursor.execute("SELECT user_id FROM user")
            found_user = self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Couldnt find any users {e}")

        if not found_user:
            self.intitial_startup()

        self.sync_database()

    # First time startup, for first user, creates all tables and initial values
    def intitial_startup(self):
        for table in tables:
            try:
                self.cursor.execute(table)
                print(f"{table} created successfully")
            except sqlite3.Error as e:
                print(f"Error creating table {e}")

        for insert in inserts:
            try:
                self.cursor.execute(insert)
                print(f"{insert} created successfully")
            except sqlite3.Error as e:
                print(f"Error creating table {e}")

        self.connection.commit()

    # Updates database to be reflective of MusicLibrary folder
    def sync_database(self):
        found_paths = []

        # Insert statement, inserts nothing if it can find a song with song_dir thats attempting to be inserted
        insert_statement = """
        INSERT INTO song (
            song_genre,
            song_artist,
            song_album,
            song_title,
            song_duration,
            song_track,
            song_dir
        )
        SELECT ?, ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 
            FROM song 
            WHERE song_dir = ?
            );
        """

        # Insert logic for each table one by one, inserting needed values to db
        for cdir_str, sdir, files in Path.walk(self.LIBRARY):
            # For each media file, grab metadata and insert into database
            # Using os.walk to work on pi, but edit to make my path.Walk logic to work
            cdir = Path(cdir_str) 
            rdir = cdir.relative_to(self.ROOT)
            for f in files:
                if f.lower().endswith((".flac", ".mp3")):  # Tuple (a, b)
                    rdir = cdir.relative_to(self.ROOT)
                    try:
                        if f.lower().endswith(".flac"):
                            audio = FLAC(str(rdir / f))  # Metadata dictionary
                        else:
                            audio = MP3(str(cdir / f))  # Metadata dictionary
                        genre = str(audio["genre"]).strip("{}[]'")
                        artist = str(audio["artist"]).strip("{}[]'")
                        album = str(audio["album"]).strip("{}[]'")
                        title = str(audio["title"]).strip("{}[]'")
                        duration = audio.info.length
                        track = str(f).split(" ")[0]
                        directory = str(rdir / f)  # Also used to see if existent
                        data = (
                            genre,
                            artist,
                            album,
                            title,
                            duration,
                            track,
                            directory,
                            directory,
                        )  # Second directory to compare to db
                        self.cursor.execute(insert_statement, data)
                        found_paths.append(
                            directory
                        )  # List of directories found on scan
                    except Exception as e:
                        print("Could not read {f}, {e}")

        self.cursor.execute("CREATE TEMP TABLE found (found_dir TEXT)")
        self.cursor.executemany(
            "INSERT INTO found VALUES (?)", [(p,) for p in found_paths]
        )
        self.cursor.execute(
            "DELETE FROM song WHERE song_dir NOT IN (SELECT found_dir FROM found)"
        )
        self.cursor.execute("DROP TABLE found")

        self.connection.commit()

    # Grabs all available playlists (name and ID)
    def get_playlists(self):
        sql = "SELECT * FROM playlist"
        self.cursor.execute(sql)
        output = self.cursor.fetchall()
        return output

    # Joins playlist_songs into a list of song_ids
    def get_playlist_songs(self, playlist_id):
        sql = "SELECT song_id FROM playlist_song WHERE playlist_id = ?"
        self.cursor.execute(sql, (playlist_id,))
        output = self.cursor.fetchall()
        return output

    # Grabs all user data, and returns in readable format
    def get_user(self, user_id):
        user_id = int(user_id) if type(user_id) == int else 0
        sql = "SELECT * FROM user JOIN settings ON user.settings_id = settings.settings_id WHERE user_id = ? "
        self.cursor.execute(sql, (user_id,))
        output = self.cursor.fetchall()[0]

        user_data = {
            "song": output[1],
            "playlist": output[3],
            "volume": output[5],
            "shuffle": output[6],
        }

        return user_data

    # Returns select query based on whether item is a song or not
    def __run_select_query(self, sql: str, params: tuple = None):
        self.cursor.execute(sql, params) if params else self.cursor.execute(sql)
        query_result = self.cursor.fetchall()  # List of tuples
        if not query_result:
            return []

        if len(query_result[0]) > 1:
            return {q[1]: q[0] for q in query_result}
        else:
            return {q[0]: i for i, q in enumerate(query_result)}

    # Query library database, grab output dependent on selecting specific item vs all of a category
    def library_query(self, btype: const.SongQueryType, params: tuple = None):
        db_id = btype.value.get("db_id")
        db_child = btype.value.get("db_child")
        if db_id == const.SongQueryType.TITLE.value.get("db_child"):
            sql = f"SELECT DISTINCT song_id, {db_child} FROM song"
        elif params and db_child == const.SongQueryType.TITLE.value.get("db_child"):
            sql = f"SELECT DISTINCT song_id, {db_child} FROM song WHERE {db_id} LIKE ?"
        elif params:
            sql = f"SELECT DISTINCT {db_child} FROM song WHERE {db_id} LIKE ?"
        else:
            sql = f"SELECT DISTINCT {db_id} FROM song"
        output = self.__run_select_query(sql, params)
        return output

    # Returns all relevant song details for UI and playback
    def get_song_details(self, song_id):
        sql = "SELECT * FROM song WHERE song_id = ?"
        self.cursor.execute(sql, (song_id,))
        output = self.cursor.fetchone()

        # Song path, and parent path (for album art)
        path = const.ROOT / output[7]
        parent_path = path.parent

        # Grab parth to album art
        art_formats = (".png", ".jpg", ".jpeg", ".webp")
        art_path = next(
            (f for f in parent_path.iterdir() if f.suffix.lower() in art_formats), None
        )

        # Readable song details
        song_details = {
            "id": output[0],
            "genre": output[1],
            "artist": output[2],
            "album": output[3],
            "title": output[4],
            "duration": output[5],
            "track_no": output[6],
            "path": path,
            "art_path": art_path,
        }

        return song_details

    # Close db connection
    def close_connection(self):
        self.connection.close()
