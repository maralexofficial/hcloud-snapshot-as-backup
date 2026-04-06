import time


class Console:
    @staticmethod
    def _ts():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def info(cls, msg):
        print(f"[{cls._ts()}] INFO  {msg}", flush=True)

    @classmethod
    def warn(cls, msg):
        print(f"[{cls._ts()}] WARN  {msg}", flush=True)

    @classmethod
    def error(cls, msg):
        print(f"[{cls._ts()}] ERROR {msg}", flush=True)

    @classmethod
    def notify(cls, title, message):
        clean_msg = message.replace("\n", " | ")
        print(f"[{cls._ts()}] NOTIFY {title} -> {clean_msg}", flush=True)
