from kivy.app import App
from kivy.clock import Clock
import ui.widgets as W
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, ScreenManager


# Library screen to navigate music files
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class HomeButton(W.ButtonTemplate):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Navigates to screen based on text of button
    def on_release(self):
        if self.debounce:
            return
        self.debounce = True

        self.app.home_nav(self.text)

        Clock.schedule_once(self.reset_debounce, 0.5)


class HomeLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
