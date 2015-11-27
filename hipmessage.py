import os
from hypchat import HypChat


class BaseFilter(object):
    # For a list of fields, check out
    # https://www.hipchat.com/docs/apiv2/method/view_room_history
    mandatory_fields = None
    without_fields = None

    def is_valid(self, message):
        '''
        This is the method the method that you should override.
        Returns whether or not the given message passes a certain
        set of conditions
        '''
        return True

    def is_ok(self, message):
        '''
        This method returns whether or not the message passed this filter
        '''
        return (
            self.has_mandatory_fields(message) and
            self.is_without_fields(message) and
            self.is_valid(message)
        )

    def has_mandatory_fields(self, msg):
        if self.mandatory_fields is None:
            return True

        keys = []
        self._get_dict_keys(msg, keys)

        return set(self.mandatory_fields).issubset(set(keys))

    def is_without_fields(self, msg):
        if self.without_fields is None:
            return True

        keys = []
        self._get_dict_keys(msg, keys)

        return not any(map(lambda key: key in keys, self.without_fields))

    def _get_dict_keys(self, dict_, result_keys):
        if isinstance(dict_, dict):
            result_keys += dict_.keys()
            map(lambda value: self._get_dict_keys(value, result_keys),
                dict_.values())


class BaseBackend(object):
    '''
    Class that exposes two methods, get_last_message_id and
    set_last_message_id. This ID is used to get the latest messages
    from a room, without getting the ones that were already processed
    '''

    def get_last_message_id(self):
        '''
        This returns the id of the last message that was saved or None
        if no message was saved so far
        '''
        raise NotImplementedError(
            "You need to implement this in your derived class")

    def set_last_message_id(self, id):
        '''
        Saves the id of the las message that was saved
        '''
        raise NotImplementedError(
            "You need to implement this in your derived class")


class FileBackend(BaseBackend):
    _FILE_PATH = '{}_last_message_db.info'
    DATE_SAVE_PATTERN = '%Y %m %d %H:%M:%S.%f'

    def __init__(self, file_path=None):
        if file_path is not None:
            self._FILE_PATH = file_path

    def _get_db_file(self):
        if os.path.isfile(self._FILE_PATH):
            return open(self._FILE_PATH, 'r')

        return None

    def get_last_message_id(self):
        file_h = self._get_db_file()
        if file_h is None:
            return None

        last_id = file_h.readline()
        last_id = last_id.strip('\n')
        file_h.close()

        return last_id or None

    def set_last_message_id(self, id_):
        with open(self._FILE_PATH, 'w') as file_h:
            file_h.write('{}\n'.format(id_))


class HipMessage(object):
    '''
    Class that gets all messages from a given room, filters them through
    the classes from filter_classes and returns them when get_newest_messages
    is called.
    '''

    # A class that has implemented two methods
    #   - set_last_message_id()
    #   - get_last_message_id()
    message_backend_class = None

    # Iterable of filter classes.
    # All messages will be passed through the is_ok method of this
    # classes and will include them only if the return Value is True
    filter_classes = None

    def __init__(self, token, room_name):
        self._token = token
        self._hipchat_client = HypChat(token)
        self._message_backend = self.message_backend_class()
        self._room_name = room_name
        self._room = self._hipchat_client.get_room(self.get_room_id(room_name))

    def get_room_id(self, room_name):
        rooms = self._hipchat_client.rooms()
        filtered_rooms = filter(
            lambda room: room['name'] == self._room_name, rooms['items'])
        if not filtered_rooms:
            raise ValueError('No room with name {}'.format(self._room_name))

        return filtered_rooms[0]['id']

    def is_message_valid(self, message):
        if self.filter_classes:
            return all(
                map(lambda cls: cls().is_ok(message), self.filter_classes))
        return True

    def get_newest_messages(self, max_results=500):
        last_message_id = self._message_backend.get_last_message_id()

        params = {}
        if last_message_id is not None:
            params = {'not_before': last_message_id}

        last_message = None
        # The messages come in the order oldest to newest
        for msg in self._room.latest(**params)['items']:
            if self.is_message_valid(msg):
                self.process_message(msg)
                last_message = msg

        if last_message is not None:
            self._message_backend.set_last_message_id(last_message['id'])

    def process_message(self, msg):
        '''
        This is the method you override in your derived class.
        Method that takes as only argument a message and processes it.
        '''

    def run(self):
        self.get_newest_messages()
