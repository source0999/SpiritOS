"""Freeze and validate the Basic Backend 10 public/private asset release."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_basic_assets import ASSET_VERSION
from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import PUBLIC_ROOT, load_basic_backend_tasks
from source_proxy.benchmarks.campaign_3_5_basic_assets.reference_validation import REFERENCE_REPORT


ROOT = Path(__file__).resolve().parents[3]
ASSET_ROOT = Path(__file__).resolve().parent
FREEZE_MANIFEST = ASSET_ROOT / "asset-freeze-manifest.json"
PRIVATE_PACKAGE_IMPORT = "source_proxy.benchmarks.campaign_3_5_basic_assets"


class BasicBackendFreezeError(ValueError):
    pass


def freeze_assets(output: Path = FREEZE_MANIFEST) -> dict[str, Any]:
    tasks = load_basic_backend_tasks()
    try:
        validation = json.loads(REFERENCE_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BasicBackendFreezeError("basic_backend_reference_report_unreadable") from error
    if (
        validation.get("schema_version")
        != "source-proxy-basic-backend-10-reference-validation/v1"
        or validation.get("task_count") != 10
        or validation.get("passed") is not True
    ):
        raise BasicBackendFreezeError("basic_backend_reference_validation_not_passed")
    _verify_production_import_boundary()
    public_files = {
        path.relative_to(ROOT).as_posix(): _sha256(path)
        for path in sorted(PUBLIC_ROOT.rglob("*"))
        if path.is_file()
    }
    private_files = {
        path.relative_to(ROOT).as_posix(): _sha256(path)
        for path in sorted(ASSET_ROOT.glob("*.py"))
        if path.name != output.name
    }
    manifest: dict[str, Any] = {
        "schema_version": "source-proxy-basic-backend-10-asset-freeze/v1",
        "asset_version": ASSET_VERSION,
        "definition_version": "source_proxy_basic_backend_10_v1",
        "validation_control_plane_commit": _git_head(),
        "task_ids": [task.task_id for task in tasks],
        "task_count": len(tasks),
        "reference_validation_sha256": _sha256(REFERENCE_REPORT),
        "production_import_boundary_passed": True,
        "public_files": public_files,
        "private_implementation_files": private_files,
    }
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**manifest, "manifest_sha256": _sha256(output)}


def validate_freeze(path: Path = FREEZE_MANIFEST) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BasicBackendFreezeError("basic_backend_freeze_manifest_unreadable") from error
    if payload.get("schema_version") != "source-proxy-basic-backend-10-asset-freeze/v1":
        raise BasicBackendFreezeError("basic_backend_freeze_manifest_invalid")
    for field in ("public_files", "private_implementation_files"):
        records = payload.get(field)
        if not isinstance(records, dict) or not records:
            raise BasicBackendFreezeError("basic_backend_freeze_manifest_invalid")
        for relative, expected in records.items():
            target = (ROOT / str(relative)).resolve(strict=True)
            if ROOT.resolve() not in target.parents or _sha256(target) != expected:
                raise BasicBackendFreezeError("basic_backend_frozen_asset_mismatch")
    if _sha256(REFERENCE_REPORT) != payload.get("reference_validation_sha256"):
        raise BasicBackendFreezeError("basic_backend_frozen_asset_mismatch")
    _verify_production_import_boundary()
    return payload


def _verify_production_import_boundary() -> None:
    source_root = ROOT / "source_proxy"
    for path in source_root.rglob("*.py"):
        relative = path.relative_to(source_root)
        if relative.parts[0] in {"benchmarks", "tests"}:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as error:
            raise BasicBackendFreezeError("basic_backend_import_boundary_unreadable") from error
        if PRIVATE_PACKAGE_IMPORT in source:
            raise BasicBackendFreezeError("basic_backend_private_assets_imported_by_production")


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main() -> int:
    manifest = freeze_assets()
    print(json.dumps({"asset_version": manifest["asset_version"], "manifest_sha256": manifest["manifest_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
