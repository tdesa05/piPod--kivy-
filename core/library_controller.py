import core.constants as const


class LibraryController:
    def __init__(self, cw, db):
        super().__init__()
        self.cw = cw
        self.db = db
        self.context = []
        self.library_history = []

    # Gets the constant buttons for the librarys home screen
    def get_library_home(self):
        data = [row for row in const.HomeScreenButton.LIBRARY.value]
        return data

    # Overwrites library history with empty list
    def reset_library_history(self):
        self.library_history = []

    # Displays last set of data shown in recycle view (can go back until at library home)
    def library_back(self):
        if len(self.library_history) < 2:
            self.reset_library_history()
            return self.get_library_home()
        else:
            # Retrieve last data
            self.library_history.remove(self.library_history[-1])
            new_data = self.library_history[-1]
        return new_data

    # Creates button data for the library recycle view
    def create_rv_data(self, button_info: dict):
        btype: const.SongQueryType = button_info.get("btype")  # Button type
        text = button_info.get("text")  # Text label on button
        has_params = button_info.get("has_params")  # Button command

        # If not library home pass tuple of params
        items = (
            self.db.library_query(btype, (text,))
            if has_params
            else self.db.library_query(btype)
        )

        new_btype = const.SongQueryType.from_db_id(btype.value.get("db_child"))
        new_has_params = (
            False
            if new_btype.value.get("db_id")
            == const.SongQueryType.TITLE.value.get("db_id")
            else True
        )

        # Create new buttons for recycleview
        data = [
            {
                "text": title,
                "item_id": i,
                "selected": False,
                "btype": new_btype,
                "has_params": new_has_params,
                "song_id": id if new_btype == const.SongQueryType.TITLE else None,
            }
            for i, (title, id) in enumerate(sorted(items.items()))
        ]
        self.library_history.append(data)
        return data
