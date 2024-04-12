import queue 


class EventConfigQueue:
    """docstring for QueueListener"""
    def __init__(self, queue):
        #self.my_name = my_name
        self.queue = queue

    def put_event(self, event):
        """Добавление события в очередь"""
        print(f"put_event - {event}")
        self.queue.put(event)

    def get_event(self):
        """Получение события из очереди"""
        try:
            event = self.queue.get_nowait()
            return event
        except queue.Empty:
            return None


    def listen_queue(self, callback_function, my_name):
        print(f"{my_name} listen_queue")
        while True:
            try:
                event_data = self.get_event()
                if event_data is not None:
                    if event_data["dst"] == my_name:
                        print(f"{my_name} получено - {event_data}")
                        callback_function(event_data)
            except queue.Empty:
                pass