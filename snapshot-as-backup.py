# Licensed under MIT

import os
import sys
import time
import signal
import socket
import threading
import queue
import requests
from cron_validator import CronScheduler

from lib.cron_humanizer import CronHumanizer
from lib.console import Console
from lib.notifications import NotificationManager
from lib.providers.ntfy import NtfyProvider
from lib.providers.smtp import SMTPProvider

os.environ["TZ"] = os.environ.get("TZ", "Europe/Berlin")
time.tzset()

base_url = "https://api.hetzner.cloud/v1"

api_token = ""
snapshot_name = ""
label_selector = ""
keep_last_default = 3

headers = {}
servers = {}
servers_keep_last = {}
snapshot_list = {}
exit_code = 0

notifier = None

hostname = os.environ.get("HOSTNAME") or socket.gethostname()

notification_queue = queue.Queue()


def notification_worker():
    while True:
        title, message = notification_queue.get()
        try:
            if notifier:
                notifier.send(message, title)
        except Exception as e:
            print(f"[ntfy] send failed: {e}")
        notification_queue.task_done()


def async_notify(title, message):
    if notifier:
        notification_queue.put((title, message))


def handle_stop(signum, frame):
    async_notify(
        f"[{hostname}] Service stopped successfully",
        f"Container stopped\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    )

    time.sleep(2)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)


def setup_notifications(
    notification_type, notifier, ntfy_config=None, smtp_config=None
):
    notification_type = (notification_type or "").lower().strip()

    if not notification_type:
        return

    types = [t.strip() for t in notification_type.split(",")]

    if "ntfy" in types and ntfy_config:
        notifier.register(
            NtfyProvider(True, ntfy_config["bin"], topic=ntfy_config["topic"])
        )

    if "smtp" in types and smtp_config:
        notifier.register(
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


def send_startup_notification(cron_string=None):
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if cron_string and cron_string.lower() != "false":
        human = CronHumanizer.describe(cron_string)
        cron_info = f"\nSchedule: {human} ({cron_string})"
    else:
        cron_info = "\nSchedule: manual run"

    message = f"Container started\nTime: {now}{cron_info}"

    async_notify(
        f"[{hostname}] Service started successfully",
        message,
    )

    Console.info("Service started successfully")
    Console.info(cron_info)


def get_servers(page=1):
    global exit_code

    url = f"{base_url}/servers?label_selector={label_selector}=true&page={page}"
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        Console.error(f"Servers Page #{page} failed: {r.reason}")
        exit_code = 1
        return

    r = r.json()
    np = r["meta"]["pagination"]["next_page"]

    for s in r["servers"]:
        servers[s["id"]] = s

        keep_last = keep_last_default
        label_key = f"{label_selector}.KEEP-LAST"

        if label_key in s["labels"]:
            keep_last = int(s["labels"][label_key])

        servers_keep_last[s["id"]] = max(1, keep_last)

    if np:
        get_servers(np)


def create_snapshot(server_id, snapshot_desc):
    global exit_code

    url = f"{base_url}/servers/{server_id}/actions/create_image"

    r = requests.post(
        url=url,
        json={
            "description": snapshot_desc,
            "type": "snapshot",
            "labels": {label_selector: ""},
        },
        headers=headers,
    )

    if not r.ok:
        Console.error(f"Snapshot failed for server {server_id}")
        exit_code = 1
    else:
        Console.success(f"Snapshot created for server {server_id}")


def get_snapshots(page=1):
    global exit_code

    url = f"{base_url}/images?type=snapshot&label_selector={label_selector}&page={page}"
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        Console.error(f"Snapshots Page #{page} failed")
        exit_code = 1
        return

    r = r.json()
    np = r["meta"]["pagination"]["next_page"]

    for img in r["images"]:
        sid = img["created_from"]["id"]
        snapshot_list.setdefault(sid, []).append(img["id"])

    if np:
        get_snapshots(np)


def delete_snapshots(snapshot_id, server_id):
    global exit_code

    url = f"{base_url}/images/{snapshot_id}"
    r = requests.delete(url=url, headers=headers)

    if not r.ok:
        Console.error(f"Delete failed #{snapshot_id}")
        exit_code = 1


def cleanup_snapshots():
    for k in snapshot_list:
        si = snapshot_list[k]
        keep_last = servers_keep_last.get(k, keep_last_default)

        if len(si) > keep_last:
            si.sort(reverse=True)

            for snapshot_id in si[keep_last:]:
                delete_snapshots(snapshot_id, k)


def run():
    global exit_code

    if not api_token:
        Console.error("API_TOKEN is missing. Aborting run.")
        return

    start_time = time.strftime("%Y-%m-%d %H:%M:%S")

    async_notify(
        f"[{hostname}] Snapshot started",
        f"Backup started\nTime: {start_time}",
    )

    Console.success(f"Snapshot job started at {start_time}")

    exit_code = 0

    servers.clear()
    servers_keep_last.clear()
    snapshot_list.clear()

    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + api_token

    get_servers()

    if not servers:
       message = f"No servers found with label        '{label_selector}'. Skipping run."
    
      Console.error(message)

    async_notify(
        f"[{hostname}] Backup skipped",
        message
    )

    return

    for server in servers:
        create_snapshot(
            server,
            snapshot_name.replace("%id%", str(server))
            .replace("%name%", servers[server]["name"])
            .replace("%timestamp%", str(int(time.time()))),
        )

    get_snapshots()
    cleanup_snapshots()

    end_time = time.strftime("%Y-%m-%d %H:%M:%S")

    status = "Success" if exit_code == 0 else "Error"

    async_notify(
        f"[{hostname}] Backup {status}",
        f"{status}\nServers: {len(servers)}\nStart: {start_time}\nEnd: {end_time}",
    )

    Console.success(
        f"Job status: {status} -> Servers: {len(servers)} | Start: {start_time} -> End: {end_time}"
    )


if __name__ == "__main__":

    IN_DOCKER_CONTAINER = os.environ.get("IN_DOCKER_CONTAINER", False)

    if IN_DOCKER_CONTAINER:
        api_token = os.environ.get("API_TOKEN")

        if not api_token:
            Console.error("API_TOKEN is not set. Exiting container.")
            sys.exit(1)

        snapshot_name = os.environ.get("SNAPSHOT_NAME", "%name%-%timestamp%")
        label_selector = os.environ.get("LABEL_SELECTOR", "AUTOBACKUP")
        keep_last_default = int(os.environ.get("KEEP_LAST", 3))

        notifier = NotificationManager()

        threading.Thread(target=notification_worker, daemon=True).start()

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

        send_startup_notification(cron_string)

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