import smtplib
from email.mime.text import MIMEText


class SMTPProvider:
    def __init__(
        self,
        enabled=False,
        host=None,
        port=587,
        user=None,
        password=None,
        sender=None,
        receiver=None,
        tls=True
    ):
        self.enabled = enabled
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender
        self.receiver = receiver
        self.tls = tls

    def is_enabled(self):
        return self.enabled

    def send(self, message, title="Hetzner Backup"):
        if not self.host or not self.receiver:
            print("SMTP not properly configured")
            return

        msg = MIMEText(message)
        msg['Subject'] = title
        msg['From'] = self.sender
        msg['To'] = self.receiver

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                if self.tls:
                    server.starttls()

                if self.user and self.password:
                    server.login(self.user, self.password)

                server.send_message(msg)

        except Exception as e:
            print(f"SMTP error: {e}")
