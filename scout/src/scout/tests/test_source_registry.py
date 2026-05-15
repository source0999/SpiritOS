import pytest

from scout.sources.storage import (
    SourceRegistryError,
    approve_candidate,
    block_candidate,
    candidate_counts,
    canonicalize_uri,
    get_candidate,
    list_candidates,
    list_registry_entries,
    record_discovery_event,
    reject_candidate,
    upsert_candidate,
)
from scout.storage.db import open_connection
from scout.storage.migrations import apply_migrations


def _db_path(tmp_path):
    db_path = tmp_path / "scout.db"
    apply_migrations(db_path)
    return db_path


def test_canonicalize_uri_normalizes_common_source_shapes():
    assert (
        canonicalize_uri("https://github.com/FastAPI/FastAPI/?utm_source=newsletter")
        == "github://fastapi/fastapi"
    )
    assert (
        canonicalize_uri("https://Example.COM/docs/?utm_source=x&lang=en#intro")
        == "https://example.com/docs?lang=en"
    )


def test_upsert_candidate_dedupes_by_canonical_uri(tmp_path):
    db_path = _db_path(tmp_path)

    first = upsert_candidate(
        db_path,
        display_uri="https://example.com/docs/?utm_source=one&lang=en",
        source_kind="docs_page",
        status="needs_review",
        confidence_score=0.72,
        reason_codes=["canonical_uri_valid"],
    )
    second = upsert_candidate(
        db_path,
        display_uri="https://EXAMPLE.com/docs?lang=en&utm_campaign=two",
        source_kind="docs_page",
        status="recommended",
        confidence_score=0.94,
        reason_codes=["canonical_uri_valid", "official_docs_pattern"],
    )

    candidates = list_candidates(db_path)

    assert second.candidate_id == first.candidate_id
    assert second.canonical_uri == "https://example.com/docs?lang=en"
    assert second.status == "recommended"
    assert second.reason_codes == ["canonical_uri_valid", "official_docs_pattern"]
    assert len(candidates) == 1
    assert candidate_counts(db_path)["recommended"] == 1


def test_approve_candidate_adds_active_registry_entry(tmp_path):
    db_path = _db_path(tmp_path)
    candidate = upsert_candidate(
        db_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
        status="recommended",
        confidence_score=0.97,
        trust_label="Official GitHub repo",
        trust_tier="official",
        metadata={"topic": "fastapi"},
    )

    entry = approve_candidate(
        db_path,
        candidate.candidate_id,
        approved_by="tester",
        poll_interval_minutes=60,
    )
    reviewed = get_candidate(db_path, candidate.candidate_id)

    assert entry.canonical_uri == "github://fastapi/fastapi"
    assert entry.status == "active"
    assert entry.approved_by == "tester"
    assert entry.poll_interval_minutes == 60
    assert entry.metadata == {"topic": "fastapi"}
    assert reviewed is not None
    assert reviewed.status == "approved"
    assert reviewed.reviewed_by == "tester"
    assert list_registry_entries(db_path, status="active") == [entry]


def test_reject_candidate_preserves_manual_state_on_later_upsert(tmp_path):
    db_path = _db_path(tmp_path)
    candidate = upsert_candidate(
        db_path,
        display_uri="https://random.example/blog",
        source_kind="blog",
    )

    rejected = reject_candidate(
        db_path,
        candidate.candidate_id,
        reason="not relevant",
        reviewed_by="tester",
    )
    rediscovered = upsert_candidate(
        db_path,
        display_uri="https://random.example/blog?utm_source=again",
        source_kind="blog",
        status="recommended",
        confidence_score=0.92,
    )

    assert rejected.status == "rejected"
    assert rejected.rejection_reason == "not relevant"
    assert rediscovered.status == "rejected"
    assert rediscovered.rejection_reason == "not relevant"


def test_block_candidate_prevents_approval_and_requeue(tmp_path):
    db_path = _db_path(tmp_path)
    candidate = upsert_candidate(
        db_path,
        display_uri="https://spam.example/tracker",
        source_kind="unknown",
        status="needs_review",
    )

    blocked = block_candidate(
        db_path,
        candidate.candidate_id,
        reason="spam pattern",
        blocked_by="tester",
    )
    rediscovered = upsert_candidate(
        db_path,
        display_uri="https://spam.example/tracker?utm_campaign=nope",
        source_kind="unknown",
        status="recommended",
        confidence_score=0.91,
    )

    assert blocked.status == "blocked"
    assert blocked.blocked_reason == "spam pattern"
    assert rediscovered.status == "blocked"
    assert rediscovered.blocked_reason == "spam pattern"
    with pytest.raises(SourceRegistryError):
        approve_candidate(db_path, candidate.candidate_id, approved_by="tester")


def test_record_discovery_event_links_to_candidate(tmp_path):
    db_path = _db_path(tmp_path)
    candidate = upsert_candidate(
        db_path,
        display_uri="https://docs.example.dev/changelog",
        source_kind="changelog",
        discovered_from_uri="https://blog.example.dev/post",
    )

    event_id = record_discovery_event(
        db_path,
        candidate_id=candidate.candidate_id,
        discovery_kind="artifact_link",
        source_uri="https://blog.example.dev/post",
        artifact_path="/tmp/artifact.md",
        raw_url="https://docs.example.dev/changelog?utm_source=blog",
        canonical_uri=candidate.canonical_uri,
        metadata={"parser": "markdown"},
    )

    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM source_discovery_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["candidate_id"] == candidate.candidate_id
    assert row["canonical_uri"] == "https://docs.example.dev/changelog"
    assert row["metadata_json"] == '{"parser": "markdown"}'
