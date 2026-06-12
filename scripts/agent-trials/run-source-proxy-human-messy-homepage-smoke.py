#!/usr/bin/env python3
"""Run a plain human messy Source Proxy homepage smoke in a disposable workspace."""

from __future__ import annotations

import argparse
import errno
import json
import os
import socket
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from source_proxy.decision.human_messy_homepage import (
    DEFAULT_HUMAN_MESSY_HOMEPAGE_PROMPT,
    DEFAULT_MODEL_ID,
    HumanMessyHomepagePaths,
    run_human_messy_homepage,
)


EVIDENCE_ROOT = REPO / "docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug"
LATEST_PATH = EVIDENCE_ROOT / "latest-run.json"
DEFAULT_PORT = 8765


def _run(prompt: str, host: str, port: int, model_id: str) -> tuple[int, dict[str, object]]:
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_root = EVIDENCE_ROOT / "runs" / run_id
    paths = HumanMessyHomepagePaths(
        workspace=run_root / "workspace",
        receipt_path=run_root / "receipt.json",
        score_path=run_root / "score.json",
        transcript_path=run_root / "raw-transcript.txt",
        diff_path=run_root / "diff-after-run.patch",
    )
    serve_port = _first_available_port(host, port)
    preview_url = f"http://{_display_host(host)}:{serve_port}/"
    score = run_human_messy_homepage(
        prompt=prompt,
        workspace=paths.workspace,
        receipt_path=paths.receipt_path,
        score_path=paths.score_path,
        transcript_path=paths.transcript_path,
        diff_path=paths.diff_path,
        preview_url=preview_url,
        model_id=model_id,
    )
    _write_workspace_files(paths.workspace, run_root / "workspace-files.txt")
    _write_json(
        LATEST_PATH,
        {
            "run_id": run_id,
            "run_root": str(run_root),
            "workspace": str(paths.workspace),
            "score_path": str(paths.score_path),
            "receipt_path": str(paths.receipt_path),
            "transcript_path": str(paths.transcript_path),
            "preview_url": preview_url,
        },
    )
    _write_text(EVIDENCE_ROOT / "preview-url.txt", preview_url + "\n")
    _print_score(score, serve_port=serve_port)
    return (0 if score["status"] == "GO" else 1), score


def _serve(host: str, port: int) -> None:
    latest = _read_latest()
    workspace = Path(latest["workspace"])
    if not workspace.is_dir():
        raise SystemExit(f"Generated workspace not found: {workspace}")
    os.chdir(workspace)
    server, actual_port = _bind_server(host, port)
    print(f"Serving workspace: {workspace}", flush=True)
    if actual_port != port:
        print(f"Requested port {port} was busy; using {actual_port}.", flush=True)
    print(f"URL: http://{_display_host(host)}:{actual_port}/", flush=True)
    server.serve_forever()


def _read_latest() -> dict[str, str]:
    if not LATEST_PATH.is_file():
        raise SystemExit("No latest run found. Run with --run first.")
    return json.loads(LATEST_PATH.read_text(encoding="utf-8"))


def _display_host(host: str) -> str:
    if host not in {"0.0.0.0", "::"}:
        return host
    lan = _lan_ip()
    return lan or "127.0.0.1"


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.0.0.1", 9))
            return str(sock.getsockname()[0])
    except OSError:
        return ""


def _bind_server(host: str, port: int) -> tuple[ThreadingHTTPServer, int]:
    for candidate in range(port, port + 20):
        try:
            return ThreadingHTTPServer((host, candidate), SimpleHTTPRequestHandler), candidate
        except OSError as error:
            if error.errno not in {errno.EADDRINUSE, 10048, 98}:
                raise
    raise OSError(errno.EADDRINUSE, f"No free port found from {port} to {port + 19}")


def _first_available_port(host: str, port: int) -> int:
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer((host, candidate), SimpleHTTPRequestHandler)
        except OSError as error:
            if error.errno not in {errno.EADDRINUSE, 10048, 98}:
                raise
            continue
        server.server_close()
        return candidate
    return port


def _write_workspace_files(workspace: Path, path: Path) -> None:
    files = []
    if workspace.exists():
        for item in workspace.rglob("*"):
            if item.is_file() and ".git" not in item.relative_to(workspace).parts:
                files.append(item.relative_to(workspace).as_posix())
    _write_text(path, "\n".join(sorted(files)) + ("\n" if files else ""))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def _print_score(score: dict[str, object], *, serve_port: int) -> None:
    print(f"status: {score['status']}")
    print(f"workspace path: {score['workspace_path']}")
    print(f"generated files: {', '.join(score.get('files_changed') or []) or 'none'}")
    print(f"preview URL: {score.get('preview_url') or ''}")
    print("preview server: not started by --run alone")
    print(
        "serve command: "
        f".venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --serve --host 0.0.0.0 --port {serve_port}"
    )
    print(f"score path: {score['workspace_path']}/../score.json")
    print(f"receipt path: {score['receipt_path']}")
    print(f"transcript path: {score['raw_transcript_path']}")
    print(f"backend_created_content: {str(score['backend_created_content']).lower()}")
    print(f"fallback_used: {str(score['fallback_used']).lower()}")
    print(f"real_app_touched: {str(score['real_app_touched']).lower()}")
    print(f"file_equals_model_action_content: {str(score['file_equals_model_action_content']).lower()}")
    print(f"actions_seen: {score['actions_seen']}")
    print(f"openable_homepage: {str(score['openable_homepage']).lower()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--prompt", default=DEFAULT_HUMAN_MESSY_HOMEPAGE_PROMPT)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    args = parser.parse_args()
    if args.run:
        exit_code, _score = _run(args.prompt, args.host, args.port, args.model_id)
        if args.serve and exit_code == 0:
            _serve(args.host, args.port)
        return exit_code
    if args.serve:
        _serve(args.host, args.port)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
