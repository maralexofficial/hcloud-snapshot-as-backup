# Licensed under MIT (https://github.com/fbrettnich/hcloud-snapshot-as-backup/blob/main/LICENSE)

import os
import sys
import json
import time
import requests
import os.path
from cron_validator import CronScheduler

from lib.providers.notifications import NotificationManager
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


def send_startup_notification():
    if not notifier or not notifier.providers:
        return

    notifier.send(
        f"Container gestartet\nZeit: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "Backup Service gestartet"
    )


def get_servers(page=1):
    global exit_code
    url = base_url + f"/servers?label_selector={label_selector}=true&page=" + str(page)
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        print(f"Servers Page #{page} could not be retrieved: {r.reason}")
        print(r.text)
        exit_code = 1
    else:
        r = r.json()
        np = r['meta']['pagination']['next_page']

        for s in r['servers']:
            servers[s['id']] = s

            keep_last = keep_last_default
            if f"{label_selector}.KEEP-LAST" in s['labels']:
                keep_last = int(s['labels'][f"{label_selector}.KEEP-LAST"])

            if keep_last < 1:
                keep_last = 1

            servers_keep_last[s['id']] = keep_last

        if np is not None:
            get_servers(np)


def create_snapshot(server_id, snapshot_desc):
    global exit_code

    url = base_url + "/servers/" + str(server_id) + "/actions/create_image"
    r = requests.post(
        url=url,
        json={"description": snapshot_desc, "type": "snapshot", "labels": {f"{label_selector}": ""}},
        headers=headers
    )

    if not r.ok:
        print(f"Snapshot for Server #{server_id} could not be created: {r.reason}")
        print(r.text)
        exit_code = 1
    else:
        image_id = r.json()['image']['id']
        print(f"Snapshot #{image_id} (Server #{server_id}) has been created")


def get_snapshots(page=1):
    global exit_code

    url = base_url + f"/images?type=snapshot&label_selector={label_selector}&page=" + str(page)
    r = requests.get(url=url, headers=headers)

    if not r.ok:
        print(f"Snapshots Page #{page} could not be retrieved: {r.reason}")
        print(r.text)
        exit_code = 1
    else:
        r = r.json()
        np = r['meta']['pagination']['next_page']

        for i in r['images']:
            sid = i['created_from']['id']
            if sid in snapshot_list:
                snapshot_list[sid].append(i['id'])
            else:
                snapshot_list[sid] = [i['id']]

        if np is not None:
            get_snapshots(np)


def cleanup_snapshots():
    for k in snapshot_list:
        si = snapshot_list[k]
        keep_last = servers_keep_last.get(k, keep_last_default)

        if len(si) > keep_last:
            si.sort(reverse=True)
            to_delete = si[keep_last:]

            for s in to_delete:
                delete_snapshots(snapshot_id=s, server_id=k)


def delete_snapshots(snapshot_id, server_id):
    global exit_code

    url = base_url + "/images/" + str(snapshot_id)
    r = requests.delete(url=url, headers=headers)

    if not r.ok:
        print(f"Snapshot #{snapshot_id} (Server #{server_id}) could not be deleted: {r.reason}")
        print(r.text)
        exit_code = 1
    else:
        print(f"Snapshot #{snapshot_id} (Server #{server_id}) was successfully deleted")


def run():
    global exit_code, notifier

    if not api_token:
        print("API token is missing... Exit.")
        sys.exit(1)

    start_time = time.strftime('%Y-%m-%d %H:%M:%S')

    if notifier:
        notifier.send(
            f"Backup gestartet\nZeit: {start_time}",
            "Backup gestartet"
        )

    exit_code = 0

    servers.clear()
    servers_keep_last.clear()
    snapshot_list.clear()

    headers['Content-Type'] = "application/json"
    headers['Authorization'] = "Bearer " + api_token

    get_servers()

    if not servers:
        print("No servers found with label")

    for server in servers:
        create_snapshot(
            server_id=server,
            snapshot_desc=str(snapshot_name)
            .replace("%id%", str(server))
            .replace("%name%", servers[server]['name'])
            .replace("%timestamp%", str(int(time.time())))
            .replace("%date%", str(time.strftime("%Y-%m-%d")))
            .replace("%time%", str(time.strftime("%H:%M:%S")))
        )

    get_snapshots()

    if not snapshot_list:
        print("No snapshots found with label")

    cleanup_snapshots()

    end_time = time.strftime('%Y-%m-%d %H:%M:%S')

    if exit_code == 0:
        title = "Backup erfolgreich"
        status = "Erfolgreich"
    else:
        title = "Backup FEHLGESCHLAGEN"
        status = "Fehler"

    msg = (
        f"{status}\n"
        f"Server: {len(servers)}\n"
        f"Start: {start_time}\n"
        f"Ende: {end_time}"
    )

    if notifier:
        notifier.send(msg, title)


if __name__ == '__main__':

    IN_DOCKER_CONTAINER = os.environ.get('IN_DOCKER_CONTAINER', False)

    if IN_DOCKER_CONTAINER:
        api_token = os.environ.get('API_TOKEN')
        snapshot_name = os.environ.get('SNAPSHOT_NAME', "%name%-%timestamp%")
        label_selector = os.environ.get('LABEL_SELECTOR', 'AUTOBACKUP')
        keep_last_default = int(os.environ.get('KEEP_LAST', 3))

        notifier = NotificationManager()

        notification_type = os.environ.get('NOTIFICATION_TYPE', '').lower()

        if not notification_type or "ntfy" in notification_type:
            ntfy_bin = os.environ.get('NTFY_BIN', "/usr/bin/ntfy-send")
            notifier.register(NtfyProvider(True, ntfy_bin))

        if not notification_type or "smtp" in notification_type:
            notifier.register(SMTPProvider(
                enabled=True,
                host=os.environ.get('SMTP_HOST'),
                port=int(os.environ.get('SMTP_PORT', 587)),
                user=os.environ.get('SMTP_USER'),
                password=os.environ.get('SMTP_PASS'),
                sender=os.environ.get('SMTP_FROM'),
                receiver=os.environ.get('SMTP_TO'),
                tls=str(os.environ.get('SMTP_TLS', 'true')).lower() == "true"
            ))

        send_startup_notification()

        cron_string = os.environ.get('CRON', '0 1 * * *')

        if cron_string is False or cron_string.lower() == 'false':
            run()
            sys.exit(exit_code)

        else:
            print(f"Starting CronScheduler [{cron_string}]...")
            cron_scheduler = CronScheduler(cron_string)

            while True:
                try:
                    if cron_scheduler.time_for_execution():
                        print("Script is now executed by cron...")
                        run()
                except KeyboardInterrupt:
                    sys.exit(0)

                time.sleep(1)

    else:
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "config.json"), "r") as config_file:
            config = json.load(config_file)

        api_token = config['api-token']
        snapshot_name = config['snapshot-name']
        label_selector = config['label-selector']
        keep_last_default = int(config['keep-last'])

        notifier = NotificationManager()

        notification_type = config.get('notification-type', '').lower()

        if not notification_type or "ntfy" in notification_type:
            notifier.register(NtfyProvider(
                True,
                config.get('ntfy-bin', "/usr/bin/ntfy-send")
            ))

        if not notification_type or "smtp" in notification_type:
            notifier.register(SMTPProvider(
                enabled=True,
                host=config.get('smtp-host'),
                port=config.get('smtp-port', 587),
                user=config.get('smtp-user'),
                password=config.get('smtp-pass'),
                sender=config.get('smtp-from'),
                receiver=config.get('smtp-to'),
                tls=config.get('smtp-tls', True)
            ))

        send_startup_notification()

        run()
        sys.exit(exit_code)
