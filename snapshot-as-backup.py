# Licensed under MIT

import os
import sys
import time
import signal
import socket

from cron_validator import CronScheduler

from lib.cron_humanizer import CronHumanizer
from lib.console import Console
from lib.notifications import NotificationManager
from lib.providers.ntfy import NtfyProvider
from lib.providers.smtp import SMTPProvider

from lib.hetzner_api import HetznerAPI
from lib.snapshot_manager import SnapshotManager

from lib.service_notifications import (
    send_start_notification,
    send_stop_notification,
)

# Timezone fix
os.environ["TZ"] = os.environ.get("TZ", "Europe/Berlin")
time.tzset()

base_url = "https://api.hetzner.cloud/v1"

api_token = ""
snapshot_name = ""
label_selector = ""
keep_last_default = 3

headers = {}
exit_code = 0

notifier = None

hostname = os.environ.get("HOSTNAME") or socket.gethostname()


def notify(title, message):
    if notifier:
        try:
            notifier.send(message, title)
        except Exception as e:
            Console.error(f"[ntfy] send failed: {e}")


def handle_stop(signum, frame):
    send_stop_notification()
    time.sleep(2)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)


def setup_notifications(
    notification_type, notifier_instance, ntfy_config=None, smtp_config=None
):
    notification_type = (notification_type or "").lower().strip()

    if not notification_type:
        return

    types = [t.strip() for t in notification_type.split(",")]

    if "ntfy" in types and ntfy_config:
        notifier_instance.register(
            NtfyProvider(True, ntfy_config["bin"], topic=ntfy_config["topic"])
        )

    if "smtp" in types and smtp_config:
        notifier_instance.register(
            SMTPProvider(
                enabled=True,
                host=smtp_config["host"],
                port=smtp_config["port"],
                user=smtp_config["user"],
                password=smtp_config["password"],
                sender=smtp_config["sender"],
                receiver=smtp_config["receiver"],
                tls=smtp_config["tls"],
            )
        )


def run():
    global exit_code

    if not api_token:
        Console.error("API_TOKEN is missing. Aborting run.")
        return

    start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    exit_code = 0

    headers.clear()
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + api_token

    api = HetznerAPI(base_url, headers, label_selector, Console)
    snapshot_manager = SnapshotManager(api, Console)

    servers = {}
    servers_keep_last = {}
    snapshot_list = {}

    servers, servers_keep_last, _ = api.get_servers(
        servers=servers,
        servers_keep_last=servers_keep_last,
        keep_last_default=keep_last_default,
    )

    if not servers:
        message = f"No servers found with label '{label_selector}'. Skipping run."
        Console.error(message)
        notify(f"[{hostname}] Snapshot skipped", message)
        return

    snapshot_manager.run_snapshots(servers, snapshot_name)

    snapshot_list, _ = api.get_snapshots(snapshot_list=snapshot_list)

    snapshot_manager.cleanup_snapshots(
        snapshot_list, servers_keep_last, keep_last_default
    )

    end_time = time.strftime("%Y-%m-%d %H:%M:%S")

    status = "Success" if exit_code == 0 else "Error"

    notify(
        f"[{hostname}] Snapshot job {status}",
        f"Snapshot job status: {status}\nServers: {len(servers)}\nStart: {start_time}\nEnd: {end_time}",
    )

    if exit_code == 0:
        Console.info(
            f"Snapshot job status: {status} -> Servers: {len(servers)} | Start: {start_time} -> End: {end_time}"
        )
    else:
        Console.error(
            f"Snapshot job status: {status} -> Servers: {len(servers)} | Start: {start_time} -> End: {end_time}\n\nJob was not successfully. Please check your hetzner cloud."
        )


if __name__ == "__main__":

    if os.environ.get("IN_DOCKER_CONTAINER", False):
        api_token = os.environ.get("API_TOKEN")

        if not api_token:
            Console.error("API_TOKEN is not set. Exiting container.")
            sys.exit(1)

        snapshot_name = os.environ.get("SNAPSHOT_NAME", "%name%-%timestamp%")
        label_selector = os.environ.get("LABEL_SELECTOR", "AUTOBACKUP")
        keep_last_default = int(os.environ.get("KEEP_LAST", 3))

        notifier = NotificationManager()

        setup_notifications(
            os.environ.get("NOTIFICATION_TYPE", ""),
            notifier,
            ntfy_config={
                "bin": os.environ.get("NTFY_BIN", "/usr/bin/ntfy-send"),
                "topic": (os.environ.get("NTFY_TOPIC") or "").strip() or "DEFAULT",
            },
            smtp_config={
                "host": os.environ.get("SMTP_HOST"),
                "port": int(os.environ.get("SMTP_PORT", 587)),
                "user": os.environ.get("SMTP_USER"),
                "password": os.environ.get("SMTP_PASS"),
                "sender": os.environ.get("SMTP_FROM"),
                "receiver": os.environ.get("SMTP_TO"),
                "tls": str(os.environ.get("SMTP_TLS", "true")).lower() == "true",
            },
        )

        cron_string = os.environ.get("CRON", "0 1 * * *")

        send_start_notification(cron_string)

        if cron_string.lower() == "false":
            run()
            sys.exit(exit_code)

        cron_scheduler = CronScheduler(cron_string)

        while True:
            if cron_scheduler.time_for_execution():
                run()
            time.sleep(1)

    else:
        Console.error("Can not run standalone either.")
