"""Database and data-integrity regression tests."""
import sqlite3

import pytest

from db.db_manager import DatabaseManager
from utils.duplicate_detector import DuplicateDetector


def _source(name="Source"):
    return {
        "name": name,
        "type": "Web",
        "link_sources": "https://example.test",
        "importance": 0.5,
        "country": "NL",
    }


def test_unified_search_binds_every_search_field(isolated_database):
    source_id = DatabaseManager.add_source(_source())
    content_id = DatabaseManager.add_content({
        "title": "Research title",
        "content_data": "needle in the text",
        "importance": 0.5,
        "sources_id": source_id,
    })
    DatabaseManager.add_content_analysis({
        "content_id": content_id,
        "classification": "needle classification",
        "list_coordinates": "52.37,4.90",
    })

    # The unified query returns one joined row; each of its bound searchable
    # columns must still find that row.
    for term in ("needle", "classification", "Research", "Source"):
        results = DatabaseManager.search_all_data_unified(term)
        assert len(results) == 1, term

    row = DatabaseManager.search_all_data_unified("needle")[0]
    assert row["content_title"] == "Research title"
    assert row["classification"] == "needle classification"


def test_advanced_search_validates_identifiers_and_nulls(isolated_database):
    DatabaseManager.add_source(_source())
    assert len(DatabaseManager.advanced_search(
        "sources",
        {"city": {"operator": "IS NULL", "value": None}},
    )) == 1

    # The public coordinates alias is translated to the current schema name.
    content_id = DatabaseManager.add_content({
        "title": "Coordinates",
        "content_data": "body",
        "importance": 0.1,
        "sources_id": 1,
    })
    DatabaseManager.add_content_analysis({
        "content_id": content_id,
        "coordinates": "10,20",
    })
    assert len(DatabaseManager.advanced_search(
        "content_analysis",
        {"coordinates": {"operator": "=", "value": "10,20"}},
    )) == 1

    with pytest.raises(ValueError):
        DatabaseManager.advanced_search(
            "sources", {"name; DROP TABLE sources": {"operator": "=", "value": "x"}}
        )
    with pytest.raises(ValueError):
        DatabaseManager.advanced_search(
            "sources", {"name": {"operator": "DROP", "value": "x"}}
        )


def test_advanced_search_preserves_repeated_fields(isolated_database):
    DatabaseManager.add_source(_source("Alpha"))
    DatabaseManager.add_source(_source("Beta"))

    results = DatabaseManager.advanced_search(
        "sources",
        {
            "name": {"operator": "=", "value": "Alpha"},
            "name__condition_2": {"operator": "=", "value": "Beta"},
            "logic": "OR",
        },
    )
    assert {row["name"] for row in results} == {"Alpha", "Beta"}


def test_backend_validation_rejects_invalid_required_fields(isolated_database):
    with pytest.raises(ValueError):
        DatabaseManager.add_source({
            "name": "A",
            "type": "Web",
            "link_sources": "not-a-url",
            "importance": 0.5,
            "country": "NL",
        })
    with pytest.raises(ValueError):
        DatabaseManager.add_content({"content_data": "body", "sources_id": 999})


def test_new_record_duplicate_detection_ignores_generated_columns(isolated_database):
    source = _source()
    DatabaseManager.add_source(source)

    # A new-form payload does not contain database-generated dates or id.
    assert DuplicateDetector.find_duplicate_source(source) is not None


def test_foreign_keys_and_delete_cascade(isolated_database):
    source_id = DatabaseManager.add_source(_source())
    content_id = DatabaseManager.add_content({
        "title": "Cascade",
        "content_data": "body",
        "importance": 0.1,
        "sources_id": source_id,
    })
    DatabaseManager.add_content_analysis({"content_id": content_id})
    assert len(DatabaseManager.get_all_content_analysis()) == 1

    DatabaseManager.delete_source(source_id)
    assert DatabaseManager.get_all_contents() == []
    assert DatabaseManager.get_all_content_analysis() == []
