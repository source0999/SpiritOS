from pathlib import Path

from scout.config import ScoutSettings
from scout.pollers.registry import load_merged_registry, register_jobs
from scout.sources.storage import approve_candidate, block_candidate, reject_candidate, upsert_candidate
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations


class FakeScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, fn, trigger, **kwargs):
        self.jobs.append({"fn": fn, "trigger": trigger, **kwargs})


def _settings(tmp_path) -> ScoutSettings:
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
version: 1
github_repos: []
rss_feeds: []
web_pages: []
""",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_path,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


def test_unapproved_rejected_and_blocked_candidates_are_not_scheduled(tmp_path):
    settings = _settings(tmp_path)
    recommended = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
        status="recommended",
    )
    rejected = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
    )
    blocked = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/openai/openai-python",
        source_kind="github_repo",
    )
    reject_candidate(
        settings.database_path,
        rejected.candidate_id,
        reason="not relevant",
        reviewed_by="tester",
    )
    block_candidate(
        settings.database_path,
        blocked.candidate_id,
        reason="blocked",
        blocked_by="tester",
    )
    scheduler = FakeScheduler()

    registry = register_jobs(scheduler, settings)

    assert recommended.status == "recommended"
    assert registry.github_repos == []
    assert scheduler.jobs == []


def test_approved_supported_sources_schedule_but_approved_web_sources_do_not(tmp_path):
    settings = _settings(tmp_path)
    github = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
    )
    rss = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/feed.xml",
        source_kind="rss_feed",
    )
    docs = upsert_candidate(
        settings.database_path,
        display_uri="https://docs.example.com/guide",
        source_kind="docs_page",
    )
    approve_candidate(settings.database_path, github.candidate_id, approved_by="tester")
    approve_candidate(settings.database_path, rss.candidate_id, approved_by="tester")
    approve_candidate(settings.database_path, docs.candidate_id, approved_by="tester")
    scheduler = FakeScheduler()

    registry = register_jobs(scheduler, settings)

    job_ids = {job["id"] for job in scheduler.jobs}
    assert job_ids == {
        "github:fastapi/fastapi:commits",
        "rss:https://example.com/feed.xml",
    }
    assert len(registry.web_pages) == 1


def test_source_gate_modules_do_not_call_coding_or_proxy_memory_paths():
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        repo_root / "scout" / "src" / "scout" / "sources",
        repo_root / "scout" / "src" / "scout" / "api" / "sources.py",
        repo_root / "src" / "app" / "api" / "scout" / "source-candidates",
    ]
    forbidden_tokens = (
        "/coding",
        "source_proxy",
        "scout-intake",
        "promotion_proxy_intake_url",
        "SOURCE_PROXY_SCOUT_INTAKE_LOG",
    )
    scanned: list[Path] = []
    for path in paths:
        if path.is_dir():
            scanned.extend(
                child
                for child in path.rglob("*")
                if child.is_file() and child.suffix in {".py", ".ts", ".tsx"}
            )
        else:
            scanned.append(path)

    offenders: list[str] = []
    for path in scanned:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(repo_root)} contains {token}")

    assert offenders == []


def test_artifact_discovery_module_has_no_network_fetch_imports():
    repo_root = Path(__file__).resolve().parents[4]
    discovery = repo_root / "scout" / "src" / "scout" / "sources" / "discovery.py"
    text = discovery.read_text(encoding="utf-8")

    assert "httpx" not in text
    assert "feedparser" not in text
    assert "poll_repo" not in text
    assert "poll_feed" not in text


def test_merged_registry_keeps_active_sources_explainable(tmp_path):
    settings = _settings(tmp_path)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
    )
    approve_candidate(
        settings.database_path,
        candidate.candidate_id,
        approved_by="tester",
        poll_interval_minutes=15,
    )

    registry = load_merged_registry(settings)

    assert len(registry.github_repos) == 1
    assert registry.github_repos[0].owner == "fastapi"
    assert registry.github_repos[0].repo == "fastapi"
    assert registry.github_repos[0].poll_interval_minutes == 15
