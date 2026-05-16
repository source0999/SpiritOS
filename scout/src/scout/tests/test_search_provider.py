import httpx

from scout.sources.search import normalize_search_sources, run_searxng_search


def test_searxng_search_returns_normalized_limited_sources():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search"
        assert request.url.params["q"] == "official FastAPI release notes"
        assert request.url.params["format"] == "json"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "FastAPI Releases",
                        "url": "https://FASTAPI.tiangolo.com/release-notes/?utm_source=x",
                        "content": "Release notes",
                    },
                    {
                        "title": "Duplicate",
                        "url": "https://fastapi.tiangolo.com/release-notes/",
                    },
                    {
                        "title": "Ignored",
                        "url": "javascript:alert(1)",
                    },
                    {
                        "title": "GitHub",
                        "url": "https://github.com/fastapi/fastapi",
                    },
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        result = run_searxng_search(
            query="official FastAPI release notes",
            base_url="http://127.0.0.1:8080",
            max_results=2,
            client=client,
        )
    finally:
        client.close()

    assert result.ok is True
    assert result.searched is True
    assert result.provider == "searxng"
    assert [source.url for source in result.sources] == [
        "https://fastapi.tiangolo.com/release-notes",
        "https://github.com/fastapi/fastapi",
    ]
    assert result.provider_trace[0].status == "used"
    assert result.provider_trace[0].source_count == 2


def test_searxng_search_handles_not_configured_without_searching():
    result = run_searxng_search(
        query="official FastAPI release notes",
        base_url=None,
        max_results=5,
    )

    assert result.ok is False
    assert result.searched is False
    assert result.error == "searxng_not_configured"
    assert result.provider_trace[0].status == "skipped"


def test_searxng_search_handles_http_and_json_failures():
    forbidden_client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(403, text="nope"))
    )
    invalid_client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text="<html>"))
    )
    try:
        forbidden = run_searxng_search(
            query="docs",
            base_url="http://127.0.0.1:8080",
            max_results=5,
            client=forbidden_client,
        )
        invalid = run_searxng_search(
            query="docs",
            base_url="http://127.0.0.1:8080",
            max_results=5,
            client=invalid_client,
        )
    finally:
        forbidden_client.close()
        invalid_client.close()

    assert forbidden.ok is False
    assert forbidden.error == "searxng_json_forbidden"
    assert invalid.ok is False
    assert invalid.error == "searxng_invalid_json"


def test_normalize_search_sources_filters_bad_urls_and_dedupes():
    sources = normalize_search_sources(
        [
            {"title": "Mail", "url": "mailto:test@example.com"},
            {"title": "Docs", "url": "https://example.com/docs?utm_medium=x"},
            {"title": "Duplicate", "url": "https://example.com/docs/"},
            {"title": "Other", "url": "https://example.com/other?b=2&a=1"},
        ],
        max_results=10,
    )

    assert [source.url for source in sources] == [
        "https://example.com/docs",
        "https://example.com/other?a=1&b=2",
    ]
