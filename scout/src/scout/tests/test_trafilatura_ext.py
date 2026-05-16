from scout.extractors.trafilatura_ext import extract_markdown


def test_extract_markdown_writes_readable_artifact(tmp_path):
    html = """
    <html><body><article><h1>Scout Test</h1><p>This is a useful article body.</p></article></body></html>
    """

    path, metadata = extract_markdown(html, "https://example.com/post", tmp_path)

    assert path is not None
    assert path.exists()
    assert "Scout Test" in path.read_text(encoding="utf-8")
    assert metadata["chars"] > 0


def test_extract_markdown_rejects_oversize(tmp_path):
    path, metadata = extract_markdown("x" * 20, "https://example.com/post", tmp_path, max_chars=10)

    assert path is None
    assert metadata["reason"] == "raw_html_oversize"
