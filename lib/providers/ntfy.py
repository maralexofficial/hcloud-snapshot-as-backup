import os
import shutil
import subprocess


class NtfyProvider:
    def __init__(self, enabled=True, bin_path=None):
        self.enabled = enabled
        
        fallback = "/usr/bin/ntfy-send"

        if not bin_path:
            bin_path = fallback

        if not shutil.which(bin_path) and not os.path.isfile(bin_path):
            print(f"[ntfy] Binary not found: {bin_path} -> fallback to {fallback}")
            bin_path = fallback

        if not shutil.which(bin_path) and not os.path.isfile(bin_path):
            print(f"[ntfy] WARNING: ntfy-send not found at {bin_path}")
            self.enabled = False

        self.bin_path = bin_path

    def send(self, message, title=""):
        if not self.enabled:
            return

        try:
            cmd = [self.bin_path]

            if title:
                cmd.extend(["-t", title])

            cmd.append(message)

            subprocess.run(cmd, check=False)

        except Exception as e:
            print(f"[ntfy] Failed to send notification: {e}")
