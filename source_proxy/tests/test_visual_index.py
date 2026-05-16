from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.vector.visual_index import (
    MAX_IMAGE_BATCH_SIZE,
    batched,
    clamp_batch_size,
    discover_image_paths,
    ingest_visual_refs,
    query_visual_refs,
)


class FakeBackend:
    embedding_dim = 3

    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    def embed_images(self, paths: list[Path]) -> list[list[float]]:
        self.batch_sizes.append(len(paths))
        return [[float(index), 0.0, 1.0] for index, _ in enumerate(paths)]

    def embed_text(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class VisualIndexTests(unittest.TestCase):
    def test_batch_size_is_clamped_to_vram_safe_limit(self) -> None:
        self.assertEqual(clamp_batch_size(99), MAX_IMAGE_BATCH_SIZE)
        self.assertEqual(clamp_batch_size(0), 1)
        self.assertEqual([len(x) for x in batched(list(range(20)), 99)], [16, 4])

    def test_discover_image_paths_ignores_hidden_and_non_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.png").write_bytes(b"")
            (root / "b.webp").write_bytes(b"")
            (root / ".hidden.jpg").write_bytes(b"")
            (root / "notes.txt").write_text("nope", encoding="utf-8")

            paths = discover_image_paths(root)

        self.assertEqual([path.name for path in paths], ["a.png", "b.webp"])

    def test_ingest_uses_clamped_batches_and_reports_no_grad_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for index in range(20):
                (root / f"{index:02d}.png").write_bytes(b"fake")
            backend = FakeBackend()

            with patch("source_proxy.vector.visual_index.write_lancedb_records") as write_records:
                summary = ingest_visual_refs(
                    refs_dir=root,
                    db_dir=Path(temp_dir) / "db",
                    batch_size=99,
                    backend=backend,
                )

        self.assertEqual(backend.batch_sizes, [16, 4])
        self.assertEqual(summary["batch_size"], 16)
        self.assertEqual(summary["record_count"], 20)
        self.assertTrue(summary["used_no_grad"])
        write_records.assert_called_once()

    def test_query_empty_index_returns_no_matches_without_embedding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = FakeBackend()

            matches = query_visual_refs(
                query="minimal dark dashboard",
                db_dir=Path(temp_dir) / "missing-db",
                backend=backend,
            )

        self.assertEqual(matches, [])
        self.assertEqual(backend.batch_sizes, [])


if __name__ == "__main__":
    unittest.main()
