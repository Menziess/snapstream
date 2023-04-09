from snapstream import Cache


def test_Cache(cache):
    """Should create working Cache instance."""
    assert isinstance(cache, Cache)

    # Rdict public methods are available on cache
    expected_attrs = set(_ for _ in dir(cache.db) if _[0] != '_')
    assert expected_attrs.issubset(set(dir(cache)))
