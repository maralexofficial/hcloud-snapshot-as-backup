import requests


class HetznerAPI:
    def __init__(self, base_url, headers, label_selector, console):
        self.base_url = base_url
        self.headers = headers
        self.label_selector = label_selector
        self.Console = console

    def get_servers(
        self, page=1, servers=None, servers_keep_last=None, keep_last_default=3
    ):
        if servers is None:
            servers = {}
        if servers_keep_last is None:
            servers_keep_last = {}

        url = f"{self.base_url}/servers?label_selector={self.label_selector}=true&page={page}"
        r = requests.get(url=url, headers=self.headers)

        if not r.ok:
            self.Console.error(f"Servers Page #{page} failed: {r.reason}")
            return servers, servers_keep_last, False

        r = r.json()

        for s in r["servers"]:
            servers[s["id"]] = s

            keep_last = keep_last_default
            label_key = f"{self.label_selector}.KEEP-LAST"

            if label_key in s["labels"]:
                keep_last = int(s["labels"][label_key])

            servers_keep_last[s["id"]] = max(1, keep_last)

        if r["meta"]["pagination"]["next_page"]:
            return self.get_servers(
                r["meta"]["pagination"]["next_page"],
                servers,
                servers_keep_last,
                keep_last_default,
            )

        return servers, servers_keep_last, True

    def create_snapshot(self, server_id, snapshot_desc):
        url = f"{self.base_url}/servers/{server_id}/actions/create_image"

        r = requests.post(
            url=url,
            json={
                "description": snapshot_desc,
                "type": "snapshot",
                "labels": {self.label_selector: ""},
            },
            headers=self.headers,
        )

        return r.ok

    def get_snapshots(self, page=1, snapshot_list=None):
        if snapshot_list is None:
            snapshot_list = {}

        url = f"{self.base_url}/images?type=snapshot&label_selector={self.label_selector}&page={page}"
        r = requests.get(url=url, headers=self.headers)

        if not r.ok:
            self.Console.error(f"Snapshots Page #{page} failed")
            return snapshot_list, False

        r = r.json()

        for img in r["images"]:
            sid = img["created_from"]["id"]
            snapshot_list.setdefault(sid, []).append(img["id"])

        if r["meta"]["pagination"]["next_page"]:
            return self.get_snapshots(
                r["meta"]["pagination"]["next_page"], snapshot_list
            )

        return snapshot_list, True

    def delete_snapshot(self, snapshot_id):
        url = f"{self.base_url}/images/{snapshot_id}"
        r = requests.delete(url=url, headers=self.headers)

        return r.ok
