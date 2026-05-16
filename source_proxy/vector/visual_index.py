from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

MAX_IMAGE_BATCH_SIZE = 16
DEFAULT_REFS_DIR = Path.home() / "Design" / "Refs"
DEFAULT_DB_DIR = Path(os.getenv("SOURCE_PROXY_DATA_DIR", "data/source-proxy")) / "visual-index"
DEFAULT_TABLE = "design_refs"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    embedding: list[float]


class VisualEmbeddingBackend(Protocol):
    embedding_dim: int

    def embed_images(self, paths: list[Path]) -> list[list[float]]:
        ...

    def embed_text(self, text: str) -> list[float]:
        ...


def ingest_visual_refs(
    *,
    refs_dir: Path = DEFAULT_REFS_DIR,
    db_dir: Path = DEFAULT_DB_DIR,
    table_name: str = DEFAULT_TABLE,
    batch_size: int = MAX_IMAGE_BATCH_SIZE,
    backend: VisualEmbeddingBackend | None = None,
) -> dict[str, object]:
    safe_batch_size = clamp_batch_size(batch_size)
    image_paths = discover_image_paths(refs_dir)
    embedder = backend or OpenClipBackend()
    records: list[dict[str, object]] = []

    for batch in batched(image_paths, safe_batch_size):
        embeddings = embedder.embed_images(batch)
        for image_path, embedding in zip(batch, embeddings, strict=True):
            records.append(
                {
                    "path": str(image_path),
                    "filename": image_path.name,
                    "vector": embedding,
                }
            )

    if records:
        write_lancedb_records(db_dir=db_dir, table_name=table_name, records=records)

    return {
        "status": "completed",
        "refs_dir": str(refs_dir),
        "db_dir": str(db_dir),
        "table_name": table_name,
        "image_count": len(image_paths),
        "record_count": len(records),
        "batch_size": safe_batch_size,
        "max_batch_size": MAX_IMAGE_BATCH_SIZE,
        "used_no_grad": True,
    }


def query_visual_refs(
    *,
    query: str,
    db_dir: Path = DEFAULT_DB_DIR,
    table_name: str = DEFAULT_TABLE,
    limit: int = 5,
    backend: VisualEmbeddingBackend | None = None,
) -> list[dict[str, object]]:
    if not lancedb_table_exists(db_dir=db_dir, table_name=table_name):
        return []
    embedder = backend or OpenClipBackend()
    query_vector = embedder.embed_text(query)
    return search_lancedb(db_dir=db_dir, table_name=table_name, vector=query_vector, limit=limit)


def discover_image_paths(refs_dir: Path) -> list[Path]:
    if not refs_dir.exists():
        return []
    return sorted(
        path
        for path in refs_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and not path.name.startswith(".")
    )


def clamp_batch_size(batch_size: int) -> int:
    if batch_size <= 0:
        return 1
    return min(batch_size, MAX_IMAGE_BATCH_SIZE)


def batched(paths: list[Path], batch_size: int) -> Iterable[list[Path]]:
    safe_batch_size = clamp_batch_size(batch_size)
    for start in range(0, len(paths), safe_batch_size):
        yield paths[start : start + safe_batch_size]


def write_lancedb_records(
    *,
    db_dir: Path,
    table_name: str,
    records: list[dict[str, object]],
) -> None:
    lancedb = _import_lancedb()
    db_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_dir))
    db.create_table(table_name, data=records, mode="overwrite")


def lancedb_table_exists(*, db_dir: Path, table_name: str) -> bool:
    if not db_dir.exists():
        return False
    lancedb = _import_lancedb()
    db = lancedb.connect(str(db_dir))
    return table_name in db.table_names()


def search_lancedb(
    *,
    db_dir: Path,
    table_name: str,
    vector: list[float],
    limit: int,
) -> list[dict[str, object]]:
    lancedb = _import_lancedb()
    db = lancedb.connect(str(db_dir))
    try:
        table = db.open_table(table_name)
    except ValueError as error:
        if "not found" in str(error).lower():
            return []
        raise
    return table.search(vector).limit(max(1, limit)).to_list()


class OpenClipBackend:
    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "laion2b_s34b_b79k",
        device: str | None = None,
    ) -> None:
        self.torch = _import_torch()
        self.open_clip = _import_open_clip()
        self.image = _import_pil_image()
        self.device = device or ("cuda" if self.torch.cuda.is_available() else "cpu")
        self.model, _, self.preprocess = self.open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self.device,
        )
        self.tokenizer = self.open_clip.get_tokenizer(model_name)
        self.model.eval()
        self.embedding_dim = int(getattr(self.model.visual, "output_dim", 512))

    def embed_images(self, paths: list[Path]) -> list[list[float]]:
        if len(paths) > MAX_IMAGE_BATCH_SIZE:
            raise ValueError(f"Image batch size must be <= {MAX_IMAGE_BATCH_SIZE}.")

        images = [
            self.preprocess(self.image.open(path).convert("RGB"))
            for path in paths
        ]
        if not images:
            return []

        with self.torch.no_grad():
            batch = self.torch.stack(images).to(self.device)
            features = self.model.encode_image(batch)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.detach().cpu().float().tolist()

    def embed_text(self, text: str) -> list[float]:
        with self.torch.no_grad():
            tokens = self.tokenizer([text]).to(self.device)
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.detach().cpu().float().tolist()[0]


def _import_lancedb():
    try:
        import lancedb
    except ImportError as error:
        raise RuntimeError(
            "lancedb is required for visual indexing. Install requirements.cuda.txt."
        ) from error
    return lancedb


def _import_torch():
    try:
        import torch
    except ImportError as error:
        raise RuntimeError(
            "torch is required for CLIP visual indexing. Install requirements.cuda.txt."
        ) from error
    return torch


def _import_open_clip():
    try:
        import open_clip
    except ImportError as error:
        raise RuntimeError(
            "open_clip_torch is required for CLIP visual indexing. Install requirements.cuda.txt."
        ) from error
    return open_clip


def _import_pil_image():
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(
            "Pillow is required for image loading. Install requirements.cuda.txt."
        ) from error
    return Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Source visual vector index utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--refs-dir", type=Path, default=DEFAULT_REFS_DIR)
    ingest_parser.add_argument("--db-dir", type=Path, default=DEFAULT_DB_DIR)
    ingest_parser.add_argument("--table", default=DEFAULT_TABLE)
    ingest_parser.add_argument("--batch-size", type=int, default=MAX_IMAGE_BATCH_SIZE)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("query")
    query_parser.add_argument("--db-dir", type=Path, default=DEFAULT_DB_DIR)
    query_parser.add_argument("--table", default=DEFAULT_TABLE)
    query_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.command == "ingest":
        payload = ingest_visual_refs(
            refs_dir=args.refs_dir,
            db_dir=args.db_dir,
            table_name=args.table,
            batch_size=args.batch_size,
        )
    else:
        matches = query_visual_refs(
            query=args.query,
            db_dir=args.db_dir,
            table_name=args.table,
            limit=args.limit,
        )
        payload = {
            "status": "completed" if matches else "empty_index",
            "db_dir": str(args.db_dir),
            "table_name": args.table,
            "matches": matches,
        }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
