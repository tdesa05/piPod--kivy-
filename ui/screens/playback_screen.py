from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.accordion import FloatLayout
from kivy.app import App
import core.constants as const
from kivy.clock import Clock
import ui.widgets as W
from kivy.uix.screenmanager import Screen, ScreenManager


# Playback screen to control currently playing music
class PlaybackScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PlaybackLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AlbumArt(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = f"{const.ROOT}/images/album/stock_album_art_1.jpg"

    def change_album_art(self, path):
        self.source = str(path)


class ScreenLabel(Label):
    pass


class PlaybackLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "None"

    def change_text(self, text):
        self.text = str(text)


class SongTitle(PlaybackLabel):
    pass


class SongArtist(PlaybackLabel):
    pass


class SongProgress(ProgressBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "None"

    def update_progress(self, value: float):
        self.value = value
