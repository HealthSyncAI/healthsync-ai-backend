class EventBroker:
    """A simple in-memory event broker."""

    def __init__(self):
        self.listeners = {}  # {event_type: [callback1, callback2, ...]}

    def subscribe(self, event_type, callback):
        """Subscribes a callback to an event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Unsubscribes a callback from an event type."""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)

    def publish(self, event):
        """Publishes an event to all subscribed listeners."""
        event_type = type(event)
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(event)  # Execute the callback
