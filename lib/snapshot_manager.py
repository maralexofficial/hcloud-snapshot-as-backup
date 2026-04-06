class SnapshotManager:
    def __init__(self, api, console):
        self.api = api
        self.Console = console

    def run_snapshots(self, servers, snapshot_name):
        for server in servers:
            desc = (
                snapshot_name.replace("%id%", str(server))
                .replace("%name%", servers[server]["name"])
                .replace("%timestamp%", str(int(__import__("time").time())))
            )

            success = self.api.create_snapshot(server, desc)

            if success:
                self.Console.success(f"Snapshot created for server {server}")
            else:
                self.Console.error(f"Snapshot failed for server {server}")

    def cleanup_snapshots(self, snapshot_list, servers_keep_last, keep_last_default):
        for server_id, snapshots in snapshot_list.items():
            keep_last = servers_keep_last.get(server_id, keep_last_default)

            if len(snapshots) > keep_last:
                snapshots.sort(reverse=True)

                for snapshot_id in snapshots[keep_last:]:
                    success = self.api.delete_snapshot(snapshot_id)

                    if not success:
                        self.Console.error(f"Delete failed #{snapshot_id}")
