from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import shutil

CONTEXT_FILE_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "CONVENTIONS.md",
    "CONTRIBUTING.md",
}


@dataclass(frozen=True)
class CapturedContextFile:
    source_path: str
    artifact_path: str
    bytes: int
    sha256: str


def _safe_name(path: Path) -> str:
    return path.as_posix().replace("/", "__").replace("\\", "__").replace(".", "_")


def _candidate_files(repo_path: Path) -> list[Path]:
    candidates: list[Path] = []
    for child in repo_path.iterdir():
        if child.is_file() and child.name in CONTEXT_FILE_NAMES:
            candidates.append(child)
        elif child.is_dir():
            if child.name == ".cursor":
                rules = child / "rules"
                if rules.is_file():
                    candidates.append(rules)
            for grandchild in child.iterdir():
                if grandchild.is_file() and grandchild.name in CONTEXT_FILE_NAMES:
                    candidates.append(grandchild)
    return candidates


def capture_context_files(
    repo_path: Path,
    owner: str,
    repo: str,
    sha7: str,
    data_dir: Path,
) -> tuple[Path, list[CapturedContextFile]]:
    out_dir = data_dir / "context_files"
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[CapturedContextFile] = []

    for source in _candidate_files(repo_path):
        rel = source.relative_to(repo_path)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        artifact_name = f"{owner}__{repo}__{sha7}__{_safe_name(rel)}"
        artifact_path = out_dir / artifact_name
        shutil.copyfile(source, artifact_path)
        records.append(
            CapturedContextFile(
                source_path=rel.as_posix(),
                artifact_path=str(artifact_path.relative_to(data_dir)),
                bytes=source.stat().st_size,
                sha256=digest,
            )
        )

    sidecar_dir = data_dir / "repomaps"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = sidecar_dir / f"{owner}__{repo}__{sha7}.context.json"
    sidecar_path.write_text(
        json.dumps([record.__dict__ for record in records], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return sidecar_path, records
