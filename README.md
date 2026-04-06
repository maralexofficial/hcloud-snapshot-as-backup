# Table of contents

* [Preface](#preface)
* [About this fork](#about-this-fork)
* [Installation](#installation)
* [Authors](#authors)
* [License](#license)

# Preface
This repository is a customized fork based on the original work from
https://github.com/fbrettnich/hcloud-snapshot-as-backup.
First of all, a big thank you and full credit to the original author for creating and sharing such a solid and useful project. The foundation and core idea of this tool come entirely from that work, and it has been a great starting point.
This fork contains personal adjustments and enhancements tailored to my own use case, but it is important to emphasize that the original implementation and inspiration belong to the original developer. Without their effort, this project would not exist in its current form.
If you find this project useful, I strongly encourage you to check out the original repository and support the author there as well.

### ⚠️ Important Notice
For any issues, bugs, or questions specifically related to this fork, please open an issue here in this repository.
Kindly avoid contacting or burdening the original author with problems related to this fork, as they are not responsible for the changes or behavior introduced here.

# About this fork
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

# Installation

### Docker image
Usecase with ntfy
```
docker run -d \
  --name hcloud-autosnapshot \
  -e API_TOKEN=your_hcloud_api_token \
  -e LABEL_SELECTOR=AUTOBACKUP \
  -e KEEP_LAST=3 \
  -e CRON="0 1 * * *" \
  -e NOTIFICATION_TYPE=ntfy \
  -e NTFY_USER=dein_user \
  -e NTFY_PASSWORD=dein_passwort \
  -e NTFY_SERVER=https://example.tld \
  -e NTFY_TOPIC=hades-notifications \
  -e NTFY_ENV_FILE=/app/.ntfy.env \
  maralexofficial/hcloud-snapshot-as-backup:latest
```

Usecase without notifications
```
docker run -d \
  --name hcloud-autosnapshot \
  -e API_TOKEN=your_hcloud_api_token \
  -e LABEL_SELECTOR=AUTOBACKUP \
  -e KEEP_LAST=3 \
  -e CRON="0 1 * * *" \
  maralexofficial/hcloud-snapshot-as-backup:latest
```

### Docker build
soon

# Quick Overview
The notification system is configured entirely via environment variables:

### Enable Notifications
```
NOTIFICATION_TYPE=ntfy,smtp
```
You can enable one or multiple providers by separating them with a comma.

### NTFY configuration
```
NTFY_USER=dein_user
NTFY_PASSWORD=dein_passwort
NTFY_SERVER=https://example.tld
NTFY_TOPIC=hades-notifications
NTFY_ENV_FILE=/app/.ntfy.env
```

### SMTP configuration
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-user
SMTP_PASS=your-password
SMTP_FROM=sender@example.com
SMTP_TO=receiver@example.com
SMTP_TLS=true
```

# Authors
soon

# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.