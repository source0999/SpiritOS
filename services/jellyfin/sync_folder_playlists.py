#!/usr/bin/env python3
"""Sync Jellyfin playlists that behave like shuffled folder queues.

This script uses the local Jellyfin database only to reuse the active local
Jellyfin Web device token. It does not print or store the token, and it does
not modify media files.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


JELLYFIN_URL = "http://127.0.0.1:8096"
JELLYFIN_DB = "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db"

FOLDER_PLAYLISTS = {
    "YES Folder Queue": "/media/yes",
    "Other Folder Queue": "/media/other",
    "Optimized Test Queue": "/media/optimized-test",
}


@dataclass(frozen=True)
class JellyfinSession:
    user_id: str
    token: str


def hyphenless(item_id: str) -> str:
    return item_id.replace("-", "").lower()


def get_session() -> JellyfinSession:
    conn = sqlite3.connect(JELLYFIN_DB)
    row = conn.execute(
        """
        select UserId, AccessToken
        from Devices
        where AccessToken is not null and AccessToken != ''
        order by DateLastActivity desc
        limit 1
        """
    ).fetchone()
    conn.close()
    if not row:
        raise RuntimeError("No Jellyfin device token found in the local database.")
    return JellyfinSession(user_id=row[0], token=row[1])


class JellyfinApi:
    def __init__(self, session: JellyfinSession) -> None:
        self.session = session
        self.headers = {
            "X-Emby-Token": session.token,
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        body: dict | None = None,
    ) -> tuple[int, str]:
        url = JELLYFIN_URL + path
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")

    def json_request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        body: dict | None = None,
    ) -> dict:
        status, text = self.request(method, path, params=params, body=body)
        if status < 200 or status >= 300:
            raise RuntimeError(f"{method} {path} failed with HTTP {status}: {text[:500]}")
        return json.loads(text) if text else {}


def load_folder_video_ids(folder_path: str) -> list[str]:
    conn = sqlite3.connect(JELLYFIN_DB)
    rows = conn.execute(
        """
        select Id
        from BaseItems
        where MediaType = 'Video'
          and IsFolder = 0
          and RunTimeTicks is not null
          and (
            Path like ?
            or Path = ?
          )
        order by SortName, Name, Path
        """,
        (folder_path.rstrip("/") + "/%", folder_path),
    ).fetchall()
    conn.close()
    return [hyphenless(row[0]) for row in rows]


def existing_playlists(api: JellyfinApi) -> dict[str, str]:
    data = api.json_request(
        "GET",
        f"/Users/{api.session.user_id}/Items",
        {"IncludeItemTypes": "Playlist", "Recursive": "true"},
    )
    return {item["Name"]: item["Id"] for item in data.get("Items", [])}


def clear_playlist(api: JellyfinApi, playlist_id: str) -> None:
    data = api.json_request(
        "GET",
        f"/Playlists/{playlist_id}/Items",
        {"UserId": api.session.user_id},
    )
    entry_ids = [
        item.get("PlaylistItemId") or item.get("Id")
        for item in data.get("Items", [])
        if item.get("PlaylistItemId") or item.get("Id")
    ]
    for start in range(0, len(entry_ids), 100):
        chunk = entry_ids[start : start + 100]
        status, text = api.request(
            "DELETE",
            f"/Playlists/{playlist_id}/Items",
            {"EntryIds": ",".join(chunk)},
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Clearing playlist failed with HTTP {status}: {text[:500]}")


def add_playlist_items(api: JellyfinApi, playlist_id: str, item_ids: list[str]) -> None:
    for start in range(0, len(item_ids), 100):
        chunk = item_ids[start : start + 100]
        status, text = api.request(
            "POST",
            f"/Playlists/{playlist_id}/Items",
            {"Ids": ",".join(chunk), "UserId": api.session.user_id},
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Adding playlist items failed with HTTP {status}: {text[:500]}")


def sync_playlist(api: JellyfinApi, name: str, folder_path: str, playlist_ids: dict[str, str]) -> None:
    item_ids = load_folder_video_ids(folder_path)
    if name in playlist_ids:
        playlist_id = playlist_ids[name]
        clear_playlist(api, playlist_id)
        action = "updated"
    else:
        result = api.json_request(
            "POST",
            "/Playlists",
            body={
                "Name": name,
                "Ids": [],
                "UserId": api.session.user_id,
                "MediaType": "Video",
                "IsPublic": False,
            },
        )
        playlist_id = result["Id"]
        action = "created"

    if item_ids:
        add_playlist_items(api, playlist_id, item_ids)

    print(f"{action}: {name}: {len(item_ids)} videos from {folder_path}")


def main() -> int:
    session = get_session()
    api = JellyfinApi(session)
    playlists = existing_playlists(api)
    for name, folder_path in FOLDER_PLAYLISTS.items():
        sync_playlist(api, name, folder_path, playlists)
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
