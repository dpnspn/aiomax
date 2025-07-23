class FSMStorage:
    def __init__(self):
        self.states: dict[int, any] = {}
        self.data: dict[int, dict] = {}

    def get_state(self, user_id: int) -> any:
        """
        Gets user's state
        """
        return self.states.get(user_id)

    def get_data(self, user_id: int, key: "any | None" = None) -> any | dict:
        """
        Gets user's data
        """
        data = self.data.get(user_id, {})
        if key is None:
            return data
        return data[key]

    def change_state(self, user_id: int, new: any):
        """
        Changes user's state
        """
        self.states[user_id] = new

    def update_data(self, user_id: int, data: "dict | None" = None, **kwdata):
        """
        Updates user's data
        """
        if data is None:
            data = {}
        self.data[user_id] = {**self.get_data(user_id), **data, **kwdata}

    def set_data(self, user_id: int, data: "dict | None" = None, **kwdata):
        """
        Sets user's data
        """

        self.data[user_id] = {**data, **kwdata}

    def clear_state(self, user_id: int) -> any:
        """
        Clears user's state and returns old
        """
        return self.states.pop(user_id, None)

    def clear_data(self, user_id: int) -> dict:
        """
        Clears user's data and returns old
        """
        return self.data.pop(user_id, {})

    def clear(self, user_id: int):
        """
        Clears user's state and data
        """
        self.states.pop(user_id, None)
        self.data.pop(user_id, {})


class FSMCursor:
    def __init__(self, storage: FSMStorage, user_id: int):
        self.storage: FSMStorage = storage
        self.user_id: int = user_id

    def get_state(self) -> any:
        """
        Gets user's state
        """
        return self.storage.get_state(self.user_id)

    def get_data(self, key: "any | None" = None) -> any | dict:
        """
        Gets user's data
        """
        return self.storage.get_data(self.user_id, key)

    def change_state(self, new: any):
        """
        Changes user's state
        """
        self.storage.change_state(self.user_id, new)

    def update_data(self, data: "dict | None" = None, **kwdata):
        """
        Updates user's data
        """
        self.storage.update_data(self.user_id, data, **kwdata)

    def set_data(self, data: "dict | None" = None, **kwdata):
        self.storage.set_data(self.user_id, data, **kwdata)

    def clear_state(self) -> any:
        """
        Deletes user's state and returns old
        """
        return self.storage.clear_state(self.user_id)

    def clear_data(self) -> dict:
        """
        Deletes user's data and returns old
        """
        return self.storage.clear_data(self.user_id)

    def clear(self):
        """
        Clears user's state and data
        """
        self.storage.clear(self.user_id)
