import os


class NotificationManager:
    def __init__(self):
        self.providers = []
        self.allowed_types = self._parse_types()

    def _parse_types(self):
        types = os.environ.get("NOTIFICATION_TYPE", "").lower().strip()

        if not types:
            return []

        return [t.strip() for t in types.split(",") if t.strip()]

    def register(self, provider):
        if not provider:
            return

        provider_name = provider.__class__.__name__.replace("Provider", "").lower()

        if self.allowed_types and provider_name not in self.allowed_types:
            return

        if hasattr(provider, "is_enabled") and provider.is_enabled():
            self.providers.append(provider)

    def send(self, message, title="Notification"):
        for provider in self.providers:
            try:
                provider.send(message, title)
            except Exception as e:
                print(f"Notification error ({provider.__class__.__name__}): {e}")
