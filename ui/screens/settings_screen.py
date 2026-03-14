from kivy.app import App
from kivy.clock import Clock
import ui.widgets as W
from kivy.uix.screenmanager import Screen, ScreenManager


# Settings screen, to edit user specific fields
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
