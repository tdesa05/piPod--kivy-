from kivy.app import App
import core.constants as const
from kivy.uix.image import Image
from kivy.uix.actionbar import Button
from kivy.uix.label import Label


class ButtonTemplate(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debounce = False
        self.app = App.get_running_app()

    def reset_debounce(self, df):
        self.debounce = False
