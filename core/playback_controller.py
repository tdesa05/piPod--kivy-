from kivy.uix.accordion import NumericProperty
from just_playback import Playback
import core.constants as const
import random
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty


class PlaybackController(EventDispatcher):
    current_song_details = ObjectProperty(None, allownone=True)
    song_position = ObjectProperty(None, allownone=True)
    shuffle = ObjectProperty(None, allownone=True)
    volume = NumericProperty(None, allownone=True)

    def __init__(self, cw, db):
        super().__init__()
        self.cw = cw
        self.db = db

        # User values (in sync with db)
        self.current_playlist = None
        self.current_song = None
        self.shuffle = False
        self.volume = 50

        # Playback instance values
        self.queue = []
        self.queue_pos = 0
        self.playlist_songs = []
        self.playlist_pos = 0

        self.debounce = False
        self.playback = Playback()
        self.progress_event = None
        self.current_song_details = {}
        self.song_position = None

    # Reset cooldown for calling playback functions
    def reset_debounce(self, df):
        self.debounce = False

    # Loads values saved in db to current instance
    def load_user_values(self, USER_ID):
        user_data = self.db.get_user(USER_ID)
        self.volume = user_data.get("volume")
        self.shuffle = user_data.get("shuffle")
        self.current_playlist = user_data.get("playlist")
        self.current_song = user_data.get("song")

    # Initialises playback object, with song, I don't alllow playlists to have duplicate songs (why would you...)
    def initialise_playback(self, song: int, context: list):
        # Randomise order of list if shuffle is enabled, otherwise play folder in order, with chosen song first
        if self.shuffle:
            random.shuffle(context)

        # Creates list of songs
        self.playlist_songs = [item for item in context]
        self.playlist_pos = self.playlist_songs.index(song)

        self.__start_song(song)

    # Append song id to a seperate object (list) of queued songs
    def queue_song(self, song: int):
        self.queue.append(song)

    # Can turn progress event on and off based on input
    def toggle_progress_event(self, start: bool):
        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None

        if start:
            self.progress_event = Clock.schedule_interval(self.song_loop, 0.2)

    # Loop that is active whilst song is playing (checking difference between song duration and progress)
    def song_loop(self, df):
        if self.playback.playing:
            self.song_position = self.playback.curr_pos / self.playback.duration
            if self.playback.duration - self.playback.curr_pos < 0.25:
                self.__next_song()

    def clear_queue(self):
        self.queue_pos = 0
        self.queue = []    

    def __play_song(self):
        self.playback.play()
        self.toggle_progress_event(True)

    def __resume_song(self):
        self.playback.resume()
        self.toggle_progress_event(True)

    def __pause_song(self):
        self.playback.pause()
        self.toggle_progress_event(False)

    # Start song based on position in song_dict
    def __start_song(self, song):
        # Get current song from position in playlist songs, and grab details
        self.current_song = song
        self.current_song_details = self.db.get_song_details(self.current_song)
        path = self.current_song_details.get("path")
        self.playback.load_file(str(path))
        self.__play_song()

    def __next_song(self):
        if self.queue:
            if self.queue_pos != len(self.queue) -1:
                self.queue_pos += 1
                self.__start_song(self.queue[self.queue_pos])
                return
        self.clear_queue()
        if self.playlist_songs:
            self.playlist_pos = (self.playlist_pos + 1) % len(self.playlist_songs)
            next_song = self.playlist_songs[self.playlist_pos]
            self.__start_song(next_song)

    def __previous_song(self):
        pass

    def __stop_song(self):
        if self.playback.playing:
            self.playback.stop()
            self.toggle_progress_event(False)

    # Handles a play/pause button with debounce for stability
    def play_pause_song(self):
        if self.debounce or not self.playback.active:
            return
        self.debounce = True

        if self.playback.playing:
            self.__pause_song()
        else:
            self.__resume_song()

        Clock.schedule_once(self.reset_debounce, 0.5)

    # User skips or goes to previous song (True = skip, False = back)
    def next_or_prev(self, skip:bool):
        if self.debounce or not self.playback.active:
            return
        self.debounce = True

        if skip:
            self.__next_song()

        # self.playback.load_file(new_song)

        Clock.schedule_once(self.reset_debounce, 0.5)
