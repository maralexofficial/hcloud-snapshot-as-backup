class CronHumanizer:
    @staticmethod
    def describe(cron: str) -> str:
        try:
            parts = cron.strip().split()
            if len(parts) != 5:
                return f"Custom cron: {cron}"

            minute, hour, day, month, weekday = parts

            if hour.startswith("*/"):
                interval = hour.replace("*/", "")
                return f"Runs every {interval} hours"

            if "," in hour:
                hours = hour.split(",")
                hours = [f"{int(h):02d}:00" for h in hours if h.isdigit()]
                return f"Runs {len(hours)}x per day at {' and '.join(hours)}"

            if hour.isdigit():
                return f"Runs daily at {int(hour):02d}:{int(minute):02d}"

            return f"Custom cron: {cron}"

        except Exception:
            return f"Custom cron: {cron}"
