from kivy.uix.accordion import BooleanProperty
from kivy.uix.accordion import ListProperty
from kivy.uix.gesturesurface import Line
from kivy.uix.accordion import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from pathlib import Path
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.properties import StringProperty, ObjectProperty
import core.constants as const
from concurrent.futures import ThreadPoolExecutor
from core.database import Database as db
from core.clickwheel import Clickwheel as cw
from core.library_controller import LibraryController as lc
from core.playback_controller import PlaybackController as pc
from kivy.core.text import LabelBase

USER_ID = 0
Window.size = (320, 240)

LabelBase.register(
    name="Helvetica",
    fn_regular=f"{const.ROOT}/fonts/Helvetica/Helvetica.ttf",
    fn_bold=f"{const.ROOT}/fonts/Helvetica/Helvetica-Bold.ttf",
)


class MainLayout(BoxLayout):
    pass


# Class of the main app
class MainApp(App):
    cw = ObjectProperty(None)  # Clickwheel
    db = ObjectProperty(None)  # Database
    lc = ObjectProperty(None)  # Playback controller
    pc = ObjectProperty(None)  # Library controller

    # Launches the mainlayout, begins app
    def build(self):
        self.cw = cw(self)
        self.db = db(USER_ID)
        self.const = const
        self.lc = lc(self.cw, self.db)
        self.pc = pc(self.cw, self.db)
        self.executor = ThreadPoolExecutor(max_workers=2)
        Window.bind(on_key_down=self.on_key_down)

        return MainLayout()

    # FOR DEVELOPMENT ONLY (keyboard functions)
    def on_key_down(self, window, keycode, scancode, text, modifiers):
        key = text
        key_dict = {
            "b": lambda: self.library_screen_back(),
            "h": lambda: self.home_nav("home"),
            "p": lambda: self.playback_control("play"),
            "s": lambda: self.playback_control("skip")
        }
        action = key_dict.get(key, None)
        if action:
            action()

    # Functions etc to load after build
    def on_start(self):
        self.pc.load_user_values(USER_ID)
        self.pc.bind(
            current_song_details=self.sync_playback_ui
        )  # Playback ui updates everytime song changes
        self.pc.bind(song_position=self.sync_playback_progress)
        self.screen_dict = {
            "home": "",
            "playback": "",
            "library": self.trigger_library_update(),
            "spotify": "",
            "settings": "",
        }

    def playback_control(self, input):
        control_dict = {
            "play": lambda: self.pc.play_pause_song(),
            "pause": lambda: self.pc.play_pause_song(),
            "skip": lambda: self.pc.next_or_prev(True)
        }
        action = control_dict.get(input)
        if action:
            action()

    # Receives cw input and triggers ui
    def cw_interaction(self, diff):
        pass

    # Loads song into playback, calls
    def trigger_playback(self, song_id):
        library_rv = self.root.ids.lrv
        context = library_rv.get_songs()
        self.executor.submit(self.load_playback, song_id, context)
        self.home_nav('playback') # Change to playback screen

    # Loads playback, based on selected song
    def load_playback(self, song_id, context):
        self.pc.initialise_playback(song_id, context)
        self.update_playback_screen()

    # Updates ui of playback screen
    @mainthread
    def sync_playback_ui(self, instance, value: dict):
        # References to kivy objects
        pb_layout = self.root.ids.pl
        pb_art = pb_layout.ids.album_art
        pb_song = pb_layout.ids.song_title
        pb_artist = pb_layout.ids.song_artist

        # Change kivy object methods
        pb_song.change_text(value.get("title"))
        pb_artist.change_text(value.get("artist"))
        pb_art.change_album_art(value.get("art_path"))
        # Do playback ui stuffs here
        pass
    
    # Updates playback progress bar to be in sync with song time
    @mainthread
    def sync_playback_progress(self, instance, value: float):
        sm = self.root.ids.sm
        if sm.current == "playback":
            pb_layout = self.root.ids.pl
            progress_bar = pb_layout.ids.song_progress
            progress_bar.update_progress(value)

    # Recieves screen name, calls setup function and switches
    def home_nav(self, screen: str, item_info=None):
        screen = screen.lower()
        sm = self.root.ids.sm
        self.screen_dict.get(screen, None)
        sm.current = screen

    # Navigates to previous screen user was on
    def library_screen_back(self):
        library_rv = self.root.ids.lrv
        self.sync_library_ui(self.lc.library_back())

    # Triggers process of updating library rv in background thread
    def trigger_library_update(self, item_info=None):
        self.executor.submit(self.fetch_library_data, item_info)

    # Updates data in the library screen, if no data given, library home is displayed
    def fetch_library_data(self, item_info=None):
        if item_info:
            data = self.lc.create_rv_data(item_info)
        else:
            data = self.lc.get_library_home()  # Resets library to home page
        self.sync_library_ui(data)

    # Updates ui of library screen
    @mainthread
    def sync_library_ui(self, data):
        if "lrv" in self.root.ids:
            library_rv = self.root.ids.lrv
            library_rv.scroll_y = 1.0
            library_rv.update_data(data)
        else:
            print("Library rv not available")


if __name__ == "__main__":
    app = MainApp()
    app.run()
