from kivy.app import App
from kivy.clock import Clock
import ui.widgets as W
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.recycleview import RecycleView


# Screen to navigate user files
class LibraryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class LibraryRV(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.data = [{"text": "Loading..."}]

    # Gets all songs in current recycleview
    def get_songs(self):
        song_ids = []
        for song in self.data:
            id = song.get("song_id", None)
            song_ids.append(id) if id else None
        return song_ids

    # Updates recycleview based on button interacted with
    def update_data(self, new_data):
        self.data = new_data


class LibraryButton(W.ButtonTemplate):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_release(self):
        if self.debounce:
            return
        self.debounce = True
        item_info = {
            "text": self.text,
            "item_id": self.item_id,
            "btype": self.btype,
            "has_params": self.has_params,
            "song_id": self.song_id,
        }

        if self.song_id:
            self.app.trigger_playback(self.song_id)
        else:
            self.app.trigger_library_update(item_info)
        Clock.schedule_once(self.reset_debounce, 0.5)
