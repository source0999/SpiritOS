from qualification_fixture.catalog import Catalog


def test_catalog_stores_values() -> None:
    catalog = Catalog()
    catalog.put("x", 1)
    assert catalog.get("x") == 1
