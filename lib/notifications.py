class NotificationManager:
    def __init__(self):
        self.providers = []

    def register(self, provider):
        if provider and provider.is_enabled():
            self.providers.append(provider)

    def send(self, message, title="Notification"):
        for provider in self.providers:
            try:
                provider.send(message, title)
            except Exception as e:
                print(f"Notification error ({provider.__class__.__name__}): {e}")
