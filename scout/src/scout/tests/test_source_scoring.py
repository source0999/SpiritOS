from scout.sources.scoring import score_candidate
from scout.sources.storage import block_candidate, upsert_candidate
from scout.storage.migrations import apply_migrations


def _db_path(tmp_path):
    db_path = tmp_path / "scout.db"
    apply_migrations(db_path)
    return db_path


def test_score_candidate_recommends_known_official_github_repo(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="github://fastapi/fastapi",
        source_kind="github_repo",
        discovered_from_uri="https://blog.python.org/feed",
    )

    assert score.status == "recommended"
    assert score.confidence_score >= 0.9
    assert "github_repo_detected" in score.reason_codes
    assert "official_repo_pattern" in score.reason_codes
    assert "linked_from_active_source" in score.reason_codes


def test_score_candidate_marks_docs_as_needs_review(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="https://docs.example.dev/guide",
        source_kind="docs_page",
        discovered_from_uri="https://blog.python.org/feed",
    )

    assert score.status == "needs_review"
    assert 0.7 <= score.confidence_score < 0.9
    assert "official_docs_pattern" in score.reason_codes
    assert score.recommendation == "Needs human review before activation."


def test_score_candidate_stores_low_evidence_blog(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="https://random.example.com/post",
        source_kind="blog",
    )

    assert score.status == "stored"
    assert score.confidence_score < 0.7


def test_score_candidate_penalizes_spam_pattern(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="https://casino-seo.example/free-money",
        source_kind="unknown",
        discovered_from_uri="https://blog.python.org/feed",
    )

    assert score.status == "stored"
    assert "spam_pattern_detected" in score.reason_codes
    assert score.confidence_score < 0.5


def test_score_candidate_detects_blocked_source(tmp_path):
    db_path = _db_path(tmp_path)
    candidate = upsert_candidate(db_path, display_uri="https://spam.example/tracker")
    block_candidate(db_path, candidate.candidate_id, reason="spam", blocked_by="tester")

    score = score_candidate(
        db_path,
        canonical_uri="https://spam.example/tracker",
        source_kind="unknown",
    )

    assert score.status == "blocked"
    assert score.confidence_score == 0.0
    assert score.reason_codes == ["blocked_source"]


def test_score_candidate_uses_structural_evidence_without_llm(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="https://fastapi.tiangolo.com/release-notes",
        source_kind="release_feed",
        discovered_from_uri="https://blog.python.org/feed",
        title="FastAPI release notes",
        snippet="Official FastAPI changelog for Python API changes.",
        published_at="2026-01-15T00:00:00+00:00",
    )

    assert score.status == "recommended"
    assert "official_domain_match" in score.reason_codes
    assert "topic_anchor_density" in score.reason_codes
    assert "source_metadata_quality" in score.reason_codes
    assert "fresh_source" in score.reason_codes


def test_score_candidate_does_not_treat_search_job_as_active_source_link(tmp_path):
    db_path = _db_path(tmp_path)

    score = score_candidate(
        db_path,
        canonical_uri="https://fastapi.tiangolo.com/release-notes",
        source_kind="release_feed",
        discovered_from_uri="search://job-id",
        title="FastAPI release notes",
    )

    assert "linked_from_active_source" not in score.reason_codes
    assert "source_metadata_quality" in score.reason_codes
