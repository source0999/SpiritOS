#!/usr/bin/env python3
"""Secret-safe SpiritFlix/Jellyfin continue-watching diagnostics for agents."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_DB = "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db"
DEFAULT_SERVER = "http://127.0.0.1:8096"


def open_db(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def seconds_from_ticks(ticks: int | None) -> int:
    return int((ticks or 0) / 10_000_000)


def format_seconds(seconds: int) -> str:
    minutes, rest = divmod(max(0, seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{rest:02d}" if hours else f"{minutes}:{rest:02d}"


def get_server_latency(server_url: str, timeout: float) -> dict[str, Any]:
    url = server_url.rstrip("/") + "/System/Info/Public"
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096)
        return {
            "ok": True,
            "status": response.status,
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "bytes": len(body),
        }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {
            "ok": False,
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "error": str(exc),
        }


def get_container_status(container: str) -> dict[str, Any]:
    try:
        output = subprocess.check_output(
            ["docker", "inspect", container, "--format", "{{.State.Status}} {{.State.Health.Status}} {{.State.StartedAt}}"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=4,
        ).strip()
        return {"ok": True, "summary": output}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def collect(connection: sqlite3.Connection, limit: int, server_url: str, timeout: float, container: str) -> dict[str, Any]:
    recent_devices = rows_to_dicts(
        connection.execute(
            """
            select Id, UserId, AppName, AppVersion, DeviceName, DeviceId, IsActive, DateLastActivity, DateModified
            from Devices
            where lower(AppName) like '%spiritflix%' or lower(DeviceName) like '%spiritflix%' or lower(DeviceId) like 'spiritflix%'
            order by datetime(DateLastActivity) desc
            limit ?
            """,
            (limit,),
        ).fetchall(),
    )

    resume_rows = rows_to_dicts(
        connection.execute(
            """
            select
              u.UserId,
              users.Username,
              u.ItemId,
              items.Name,
              items.SeriesName,
              items.Type,
              items.MediaType,
              items.Path,
              items.TopParentId,
              top.Name as TopParentName,
              u.PlaybackPositionTicks,
              u.Played,
              u.IsFavorite,
              u.PlayCount,
              u.LastPlayedDate
            from UserData u
            left join BaseItems items on items.Id = u.ItemId
            left join BaseItems top on top.Id = items.TopParentId
            left join Users users on users.Id = u.UserId
            where u.PlaybackPositionTicks > 0 and u.Played = 0
            order by datetime(u.LastPlayedDate) desc
            limit ?
            """,
            (limit,),
        ).fetchall(),
    )

    favorite_rows = rows_to_dicts(
        connection.execute(
            """
            select
              u.UserId,
              users.Username,
              u.ItemId,
              items.Name,
              items.Type,
              items.Path,
              top.Name as TopParentName,
              u.LastPlayedDate
            from UserData u
            left join BaseItems items on items.Id = u.ItemId
            left join BaseItems top on top.Id = items.TopParentId
            left join Users users on users.Id = u.UserId
            where u.IsFavorite = 1
            order by coalesce(items.SortName, items.Name) collate nocase
            limit ?
            """,
            (limit,),
        ).fetchall(),
    )

    detached_resume_count = connection.execute(
        """
        select count(*)
        from UserData u
        left join BaseItems items on items.Id = u.ItemId
        where u.PlaybackPositionTicks > 0 and u.Played = 0 and items.Id is null
        """,
    ).fetchone()[0]

    duplicate_resume_rows = rows_to_dicts(
        connection.execute(
            """
            select ItemId, count(*) as Rows, max(LastPlayedDate) as NewestLastPlayedDate
            from UserData
            where PlaybackPositionTicks > 0 and Played = 0
            group by ItemId
            having count(*) > 1
            order by Rows desc, datetime(NewestLastPlayedDate) desc
            limit ?
            """,
            (limit,),
        ).fetchall(),
    )

    resume_by_library = Counter(row.get("TopParentName") or "(detached/no library)" for row in resume_rows)
    resume_by_path_root = Counter((row.get("Path") or "(no path)").split("/")[2] if (row.get("Path") or "").startswith("/media/") else "(non-media/no path)" for row in resume_rows)

    return {
        "db": str(Path(DEFAULT_DB)),
        "server": {
            "publicInfo": get_server_latency(server_url, timeout),
            "container": get_container_status(container),
        },
        "recentSpiritFlixDevices": recent_devices,
        "resumeSummary": {
            "recentRows": len(resume_rows),
            "detachedRows": detached_resume_count,
            "byLibrary": dict(resume_by_library),
            "byMediaRoot": dict(resume_by_path_root),
            "duplicates": duplicate_resume_rows,
        },
        "recentResumeRows": resume_rows,
        "recentFavoriteRows": favorite_rows,
    }


def print_report(data: dict[str, Any]) -> None:
    server = data["server"]
    print("SpiritFlix Continue Diagnostics")
    print(f"Public info: {server['publicInfo']}")
    print(f"Container: {server['container']}")
    print()

    print("Recent SpiritFlix devices")
    for device in data["recentSpiritFlixDevices"]:
        print(f"- {device['DeviceName']} {device['DeviceId']} active={device['IsActive']} last={device['DateLastActivity']}")
    if not data["recentSpiritFlixDevices"]:
        print("- none")
    print()

    summary = data["resumeSummary"]
    print("Resume lane summary")
    print(f"- detached rows: {summary['detachedRows']}")
    print(f"- by library: {summary['byLibrary']}")
    print(f"- by media root: {summary['byMediaRoot']}")
    print(f"- duplicate item rows: {len(summary['duplicates'])}")
    print()

    print("Recent resume rows")
    for row in data["recentResumeRows"]:
        title = row["SeriesName"] or row["Name"] or row["ItemId"]
        position = format_seconds(seconds_from_ticks(row["PlaybackPositionTicks"]))
        library = row["TopParentName"] or "(detached/no library)"
        print(f"- {row['LastPlayedDate']} {position} [{library}] {title} :: {row['Path']}")
    if not data["recentResumeRows"]:
        print("- none")
    print()

    print("Recent favorites")
    for row in data["recentFavoriteRows"]:
        library = row["TopParentName"] or "(detached/no library)"
        print(f"- [{library}] {row['Name'] or row['ItemId']} :: {row['Path']}")
    if not data["recentFavoriteRows"]:
        print("- none")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect SpiritFlix/Jellyfin resume, favorite, device, and latency state.")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to jellyfin.db on the Jellyfin host.")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Jellyfin server URL reachable from this machine.")
    parser.add_argument("--container", default="spirit-jellyfin", help="Jellyfin container name for docker inspect.")
    parser.add_argument("--limit", type=int, default=12, help="Rows to print per section.")
    parser.add_argument("--timeout", type=float, default=3.0, help="HTTP/docker timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    args = parser.parse_args()

    connection = open_db(args.db)
    try:
        data = collect(connection, args.limit, args.server, args.timeout, args.container)
        data["db"] = args.db
    finally:
        connection.close()

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_report(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
