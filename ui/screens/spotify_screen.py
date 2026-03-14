from kivy.app import App
from kivy.clock import Clock
import ui.widgets as W
from kivy.uix.screenmanager import Screen, ScreenManager


# Spotify screen to navigate spotify library
class SpotifyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
