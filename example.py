from hipmessage import BaseFilter, HipMessage, FileBackend


class MyFilter(BaseFilter):
    mandatory_fields = ['message_links']


class MyHipchatMessageFilterer(HipMessage):
    message_backend_class = FileBackend
    filter_classes = (MyFilter,)

    def process_message(self, msg):
        import pprint
        pprint.pprint(msg)


instance = MyHipchatMessageFilterer('your_token_here', 'Tech_stuff')
instance.run()
