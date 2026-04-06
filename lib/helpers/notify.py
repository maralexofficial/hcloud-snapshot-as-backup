from lib.console import Console


def notify(notifier, title, message):
    if not notifier:
        return

    try:
        notifier.send(message, title)
    except Exception as e:
        Console.error(f"[notification] failed: {e}")
