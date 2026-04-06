### Notice
This repository is a customized fork based on the original work from
https://github.com/fbrettnich/hcloud-snapshot-as-backup⁠�.
First of all, a big thank you and full credit to the original author for creating and sharing such a solid and useful project. The foundation and core idea of this tool come entirely from that work, and it has been a great starting point.
This fork contains personal adjustments and enhancements tailored to my own use case, but it is important to emphasize that the original implementation and inspiration belong to the original developer. Without their effort, this project would not exist in its current form.
If you find this project useful, I strongly encourage you to check out the original repository and support the author there as well.

### ⚠️ Important Notice:
For any issues, bugs, or questions specifically related to this fork, please open an issue here in this repository.
Kindly avoid contacting or burdening the original author with problems related to this fork, as they are not responsible for the changes or behavior introduced here.

### Key Changes in This Fork
The most significant enhancement in this fork compared to the original project is the extended notification system.
While the original implementation focuses primarily on snapshot creation and cleanup, this fork introduces a flexible and extensible notification layer that allows you to stay informed about the container’s activity in real time.
Notification System
This fork supports multiple notification providers, which can be used individually or in combination:
ntfy – lightweight push notifications via a simple HTTP-based system
SMTP (Email) – traditional email notifications for detailed reporting
The system is designed in a modular way, making it easy to extend or adapt to additional notification providers in the future.

### Features of the Notification System
* 📢 Notifications on startup, shutdown, and snapshot execution
* ⏭️ Notifications when a run is skipped (e.g. no matching servers found)
* ✅ Clear success and error reporting after each run
* ⚙️ Configurable via environment variables
* 🔄 Asynchronous sending to avoid blocking the main process

## Setup (Quick Overview)
The notification system is configured entirely via environment variables:

##### Enable Notifications
```
NOTIFICATION_TYPE=ntfy,smtp
```
You can enable one or multiple providers by separating them with a comma.

##### ntfy Configuration
```
NTFY_USER=dein_user
NTFY_PASSWORD=dein_passwort
NTFY_SERVER=https://example.tld
NTFY_TOPIC=hades-notifications
NTFY_ENV_FILE=/app/.ntfy.env
```

##### SMTP Configuration
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-user
SMTP_PASS=your-password
SMTP_FROM=sender@example.com
SMTP_TO=receiver@example.com
SMTP_TLS=true
```
