from hipmessage import BaseFilter, HipMessage, FileBackend
import re
import json


class MessagesWithCards(BaseFilter):
    # Get all messages that have a card
    mandatory_fields = ['card']

    def is_valid(self, message):
        # Get only those that represent a link
        # This needs to be fixed; cards come as string
        card = json.loads(message['card'])
        return card['style'] == 'link'


class CardHipMessages(HipMessage):
    message_backend_class = FileBackend
    filter_classes = (MessagesWithCards,)

    def process_message(self, msg):
        card = json.loads(msg['card'])
        print 'Description: {} | Link: {}'.format(
            card['description'].encode('utf8'), card['url'].encode('utf8'))


instance = CardHipMessages(
    '', 'Tech_stuff')
instance.run()
