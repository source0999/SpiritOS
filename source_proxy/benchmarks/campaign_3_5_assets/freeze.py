"""Freeze a companion Campaign 3.5 asset release after the readiness gate passes."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ASSET_VERSION = "source_proxy_coder_backend_assets_v1.1.0"
ROOT = Path(__file__).resolve().parents[3]
ASSET_ROOT = Path(__file__).resolve().parent


def _command(*args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, env=env).strip()


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def freeze(output: Path) -> dict[str, object]:
    readiness = json.loads((ASSET_ROOT / "readiness-report.json").read_text(encoding="utf-8"))
    if not readiness["passed"]:
        raise RuntimeError("campaign_3_5_asset_readiness_gate_not_passed")
    files = {
        path.relative_to(ROOT).as_posix(): _sha256(path)
        for path in sorted(ASSET_ROOT.rglob("*"))
        if path.is_file() and path.name not in {output.name} and "__pycache__" not in path.parts
    }
    rust_env = {**os.environ, "CARGO_HOME": "/home/source/.campaign-3-5-tools/cargo", "RUSTUP_HOME": "/home/source/.campaign-3-5-tools/rustup", "RUSTUP_TOOLCHAIN": "stable"}
    manifest = {
        "schema_version": "campaign-3.5-asset-freeze/v1",
        "asset_version": ASSET_VERSION,
        "definition_version": "source_proxy_coder_backend_100_v1.1",
        "validation_commit": _command("git", "rev-parse", "HEAD"),
        "readiness": readiness,
        "runtime_versions": {
            "python": _command("python3", "--version"),
            "node": _command("node", "--version"),
            "typescript": _command(str(ROOT / "node_modules/.bin/tsc"), "--version"),
            "go": _command("/home/source/.campaign-3-5-tools/go/bin/go", "version"),
            "rustc": _command("/home/source/.campaign-3-5-tools/cargo/bin/rustc", "--version", env=rust_env),
            "black": _command("python3", "-m", "black", "--version", env={**os.environ, "PYTHONPATH": "/home/source/.campaign-3-5-tools/python"}),
            "cryptography": _command("python3", "-c", "import cryptography; print(cryptography.__version__)", env={**os.environ, "PYTHONPATH": "/home/source/.campaign-3-5-tools/python"}),
        },
        "files": files,
    }
    serialized = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    output.write_text(serialized, encoding="utf-8")
    return {**manifest, "manifest_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}


def main() -> int:
    output = ASSET_ROOT / "asset-freeze-manifest.json"
    result = freeze(output)
    print(json.dumps({"asset_version": result["asset_version"], "manifest_sha256": result["manifest_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
