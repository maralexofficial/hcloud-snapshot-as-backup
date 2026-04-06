# Licensed under MIT (https://github.com/fbrettnich/hcloud-snapshot-as-backup/blob/main/LICENSE)

import os
import sys
import json
import time
import signal
import socket
import threading
import queue
import requests
import os.path
from cron_validator import CronScheduler

from lib.notifications import NotificationManager
from lib.providers.ntfy import NtfyProvider
from lib.providers.smtp import SMTPProvider

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
hostname = (
    os.environ.get("HOSTNAME")
    or os.environ.get("COMPOSE_PROJECT_NAME")
    or socket.gethostname()
)

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

    time.sleep(1)

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


def send_startup_notification():
    async_notify(
        f"[{hostname}] Service started successfully",
        f"Container started\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    )


def get_servers(page=1):
    global exit_code
    url = base_url + f"/servers?label_selector={label_selector}=true&page=" + str(page)
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        print(f"Servers Page #{page} could not be retrieved: {r.reason}")
        exit_code = 1
    else:
        r = r.json()
        np = r["meta"]["pagination"]["next_page"]

        for s in r["servers"]:
            servers[s["id"]] = s

            keep_last = keep_last_default
            if f"{label_selector}.KEEP-LAST" in s["labels"]:
                keep_last = int(s["labels"][f"{label_selector}.KEEP-LAST"])

            if keep_last < 1:
                keep_last = 1

            servers_keep_last[s["id"]] = keep_last

        if np is not None:
            get_servers(np)


def create_snapshot(server_id, snapshot_desc):
    global exit_code

    url = base_url + "/servers/" + str(server_id) + "/actions/create_image"
    r = requests.post(
        url=url,
        json={
            "description": snapshot_desc,
            "type": "snapshot",
            "labels": {f"{label_selector}": ""},
        },
        headers=headers,
    )

    if not r.ok:
        print(f"Snapshot for Server #{server_id} failed")
        exit_code = 1
    else:
        print(f"Snapshot created for Server #{server_id}")


def get_snapshots(page=1):
    global exit_code

    url = (
        base_url
        + f"/images?type=snapshot&label_selector={label_selector}&page="
        + str(page)
    )
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        print(f"Snapshots Page #{page} failed")
        exit_code = 1
    else:
        r = r.json()
        np = r["meta"]["pagination"]["next_page"]

        for i in r["images"]:
            sid = i["created_from"]["id"]
            snapshot_list.setdefault(sid, []).append(i["id"])

        if np is not None:
            get_snapshots(np)


def cleanup_snapshots():
    for k in snapshot_list:
        si = snapshot_list[k]
        keep_last = servers_keep_last.get(k, keep_last_default)

        if len(si) > keep_last:
            si.sort(reverse=True)
            for s in si[keep_last:]:
                delete_snapshots(s, k)


def delete_snapshots(snapshot_id, server_id):
    global exit_code

    url = base_url + "/images/" + str(snapshot_id)
    r = requests.delete(url=url, headers=headers)

    if not r.ok:
        print(f"Delete failed #{snapshot_id}")
        exit_code = 1


def run():
    global exit_code

    start_time = time.strftime("%Y-%m-%d %H:%M:%S")

    async_notify(
        f"[{hostname}] Backup started",
        f"Backup started\nTime: {start_time}",
    )

    exit_code = 0

    servers.clear()
    servers_keep_last.clear()
    snapshot_list.clear()

    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + api_token

    get_servers()

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

    msg = (
        f"{status}\n"
        f"Servers: {len(servers)}\n"
        f"Start: {start_time}\n"
        f"End: {end_time}"
    )

    async_notify(f"[{hostname}] Backup {status}", msg)


if __name__ == "__main__":

    IN_DOCKER_CONTAINER = os.environ.get("IN_DOCKER_CONTAINER", False)

    if IN_DOCKER_CONTAINER:
        api_token = os.environ.get("API_TOKEN")
        snapshot_name = os.environ.get("SNAPSHOT_NAME", "%name%-%timestamp%")
        label_selector = os.environ.get("LABEL_SELECTOR", "AUTOBACKUP")
        keep_last_default = int(os.environ.get("KEEP_LAST", 3))

        notifier = NotificationManager()

        worker = threading.Thread(target=notification_worker, daemon=True)
        worker.start()

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

        send_startup_notification()

        cron_string = os.environ.get("CRON", "0 1 * * *")

        if cron_string.lower() == "false":
            run()
            sys.exit(exit_code)

        cron_scheduler = CronScheduler(cron_string)

        while True:
            if cron_scheduler.time_for_execution():
                run()
            time.sleep(1)

    else:
        print("Standalone mode not shown here")
