import subprocess
import shutil


class NtfyProvider:
    def __init__(self, enabled=False, binary="/usr/bin/ntfy-send"):
        self.enabled = enabled
        self.binary = binary

    def is_enabled(self):
        return self.enabled

    def is_available(self):
        return shutil.which(self.binary) is not None

    def send(self, message, title="Hetzner Backup"):
        if not self.is_available():
            print(f"ntfy binary not found: {self.binary}")
            return

        subprocess.run(
            [self.binary, "-t", title, message],
            check=True
        )
