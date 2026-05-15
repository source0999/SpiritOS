from pathlib import Path
from urllib.parse import urlparse
import hashlib

import trafilatura


def extract_markdown(
    raw_html: str,
    source_uri: str,
    data_dir: Path,
    *,
    max_chars: int = 500_000,
) -> tuple[Path | None, dict]:
    """Extract clean Markdown from raw HTML and persist it under data/extracted."""
    if len(raw_html) > max_chars:
        return None, {"reason": "raw_html_oversize", "raw_chars": len(raw_html)}
    md = trafilatura.extract(
        raw_html,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        deduplicate=True,
        favor_recall=False,
    )
    if not md:
        return None, {"reason": "extractor_empty"}
    digest = hashlib.sha256(md.encode("utf-8")).hexdigest()[:16]
    host = (urlparse(source_uri).hostname or "unknown").replace(":", "_")
    out_dir = data_dir / "extracted" / host
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{digest}.md"
    out_path.write_text(md, encoding="utf-8")
    return out_path, {"chars": len(md), "sha": digest}
