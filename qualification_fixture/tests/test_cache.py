from qualification_fixture.cache import BoundedCache


def test_cache_is_bounded_and_evicts_oldest() -> None:
    cache = BoundedCache(max_entries=2, ttl_seconds=10, now=lambda: 0)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
