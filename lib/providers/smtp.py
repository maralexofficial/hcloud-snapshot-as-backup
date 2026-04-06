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
        return self.enabled and self.host and self.receiver

    def send(self, message, title="Notification"):
        if not self.is_enabled():
            return

        try:
            msg = MIMEText(message)
            msg['Subject'] = title
            msg['From'] = self.sender or self.user
            msg['To'] = self.receiver

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.ehlo()

                if self.tls:
                    server.starttls()
                    server.ehlo()

                if self.user and self.password:
                    server.login(self.user, self.password)

                server.send_message(msg)

        except Exception as e:
            print(f"[smtp] Error sending notification: {e}")
