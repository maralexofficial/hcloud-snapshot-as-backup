import os
import shutil
import subprocess


class NtfyProvider:
    def __init__(self, enabled=True, bin_path=None):
        self._enabled = enabled

        fallback = "/usr/bin/ntfy-send"

        if not bin_path:
            bin_path = fallback

        if not self._is_valid_bin(bin_path):
            print(f"[ntfy] Binary not found: {bin_path} -> fallback to {fallback}")
            bin_path = fallback

        if not self._is_valid_bin(bin_path):
            print(f"[ntfy] WARNING: ntfy-send not found at {bin_path}")
            self._enabled = False

        self.bin_path = bin_path

        self.topic = "DEFAULT"
        self.title = None
        self.priority = None
        self.tags = None

    def _is_valid_bin(self, path):
        return bool(shutil.which(path) or os.path.isfile(path))

    def is_enabled(self):
        return self._enabled

    def send(self, message, title=None):
        if not self._enabled:
            return

        try:
            cmd = [self.bin_path]

            if self.topic:
                cmd.append(self.topic)

            if title:
                cmd.append(title)
            elif self.title:
                cmd.append(self.title)

            cmd.append(message)

            if self.priority:
                cmd.append(f"--prio={self.priority}")

            if self.tags:
                cmd.append(f"--tags={self.tags}")

            subprocess.run(cmd, check=False)

        except Exception as e:
            print(f"[ntfy] Failed to send notification: {e}")
