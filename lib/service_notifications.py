import time

from lib.console import Console
from lib.cron_humanizer import CronHumanizer


def send_stop_notification(notify, hostname, notifier):
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    notify(
        notifier,
        f"[{hostname}] Service stopped successfully",
        f"Container stopped\nTime: {now}",
    )

    Console.success("Service stopped successfully")


def send_start_notification(notify, hostname, notifier, cron_string=None):
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if cron_string and cron_string.lower() != "false":
        human = CronHumanizer.describe(cron_string)
        cron_info = f"\nSchedule: {human} ({cron_string})"
    else:
        cron_info = "\nSchedule: manual run"

    notify(
        notifier,
        f"[{hostname}] Service started successfully",
        f"Container started\nTime: {now}{cron_info}",
    )

    Console.success("Service started successfully")
    Console.success(cron_info)
