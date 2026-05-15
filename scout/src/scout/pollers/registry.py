from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel, Field, HttpUrl
import structlog
import yaml

from scout.config import ScoutSettings
from scout.pollers.github import poll_repo
from scout.pollers.rss import poll_feed
from scout.sources.models import SourceRegistryEntry
from scout.sources.storage import list_registry_entries

logger = structlog.get_logger()

_OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class GithubRepoSource(BaseModel):
    owner: str
    repo: str
    poll_interval_minutes: int = Field(ge=1)


class RssFeedSource(BaseModel):
    url: HttpUrl
    poll_interval_minutes: int = Field(ge=1)
    regex_exclude: list[str] = Field(default_factory=list)


class WebPageSource(BaseModel):
    url: HttpUrl
    poll_interval_minutes: int = Field(ge=1)


class SourceRegistry(BaseModel):
    version: int
    github_repos: list[GithubRepoSource] = Field(default_factory=list)
    rss_feeds: list[RssFeedSource] = Field(default_factory=list)
    web_pages: list[WebPageSource] = Field(default_factory=list)


def load_registry(path: Path) -> SourceRegistry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry = SourceRegistry.model_validate(raw)
    for repo in registry.github_repos:
        if not _OWNER_REPO_RE.fullmatch(repo.owner) or not _OWNER_REPO_RE.fullmatch(repo.repo):
            raise ValueError(f"invalid GitHub source name: {repo.owner}/{repo.repo}")
    for feed in registry.rss_feeds:
        if feed.url.scheme != "https":
            raise ValueError(f"RSS feed must use https: {feed.url}")
    for page in registry.web_pages:
        if page.url.scheme != "https":
            raise ValueError(f"web page must use https: {page.url}")
    return registry


def load_merged_registry(settings: ScoutSettings) -> SourceRegistry:
    registry = load_registry(settings.config_path)
    active_sources = list_registry_entries(settings.database_path, status="active")
    return merge_active_sources(registry, active_sources)


def merge_active_sources(
    registry: SourceRegistry,
    active_sources: list[SourceRegistryEntry],
) -> SourceRegistry:
    github_keys = {(source.owner.lower(), source.repo.lower()) for source in registry.github_repos}
    rss_urls = {str(source.url).rstrip("/") for source in registry.rss_feeds}
    web_urls = {str(source.url).rstrip("/") for source in registry.web_pages}
    github_repos = list(registry.github_repos)
    rss_feeds = list(registry.rss_feeds)
    web_pages = list(registry.web_pages)

    for source in active_sources:
        interval = source.poll_interval_minutes or 60
        if source.source_kind == "github_repo":
            github_source = _github_source_from_registry(source, interval)
            if github_source is None:
                continue
            key = (github_source.owner.lower(), github_source.repo.lower())
            if key in github_keys:
                continue
            github_keys.add(key)
            github_repos.append(github_source)
            continue

        if source.source_kind == "rss_feed":
            rss_source = _rss_source_from_registry(source, interval)
            if rss_source is None:
                continue
            key = str(rss_source.url).rstrip("/")
            if key in rss_urls:
                continue
            rss_urls.add(key)
            rss_feeds.append(rss_source)
            continue

        if source.source_kind in {"web_page", "docs_page", "blog", "changelog", "release_feed"}:
            web_source = _web_source_from_registry(source, interval)
            if web_source is None:
                continue
            key = str(web_source.url).rstrip("/")
            if key in web_urls:
                continue
            web_urls.add(key)
            web_pages.append(web_source)

    return SourceRegistry(
        version=registry.version,
        github_repos=github_repos,
        rss_feeds=rss_feeds,
        web_pages=web_pages,
    )


def _github_source_from_registry(
    source: SourceRegistryEntry,
    interval: int,
) -> GithubRepoSource | None:
    if not source.canonical_uri.startswith("github://"):
        return None
    parts = [part for part in source.canonical_uri.removeprefix("github://").split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[:2]
    if not _OWNER_REPO_RE.fullmatch(owner) or not _OWNER_REPO_RE.fullmatch(repo):
        return None
    return GithubRepoSource(owner=owner, repo=repo, poll_interval_minutes=interval)


def _rss_source_from_registry(
    source: SourceRegistryEntry,
    interval: int,
) -> RssFeedSource | None:
    uri = source.display_uri or source.canonical_uri
    try:
        return RssFeedSource(url=uri, poll_interval_minutes=interval)
    except Exception:
        return None


def _web_source_from_registry(
    source: SourceRegistryEntry,
    interval: int,
) -> WebPageSource | None:
    uri = source.display_uri or source.canonical_uri
    try:
        return WebPageSource(url=uri, poll_interval_minutes=interval)
    except Exception:
        return None


async def _run_github_job(
    scheduler: AsyncIOScheduler,
    job_id: str,
    owner: str,
    repo: str,
    endpoint: str,
    settings: ScoutSettings,
) -> None:
    result = await poll_repo(owner, repo, endpoint, settings=settings)
    logger.info("github_poll_complete", job_id=job_id, result=result.__dict__)
    if result.pause_source:
        scheduler.pause_job(job_id)
        logger.warning("poll_job_paused", job_id=job_id, source_uri=result.source_uri)
    elif result.next_run_epoch is not None:
        scheduler.modify_job(
            job_id,
            next_run_time=datetime.fromtimestamp(result.next_run_epoch, tz=timezone.utc),
        )


async def _run_rss_job(
    scheduler: AsyncIOScheduler,
    job_id: str,
    url: str,
    regex_exclude: list[str],
    settings: ScoutSettings,
) -> None:
    result = await poll_feed(url, regex_exclude=regex_exclude, settings=settings)
    logger.info("rss_poll_complete", job_id=job_id, result=result.__dict__)
    if result.pause_source:
        scheduler.pause_job(job_id)
        logger.warning("poll_job_paused", job_id=job_id, source_uri=result.source_uri)


def register_jobs(scheduler: AsyncIOScheduler, settings: ScoutSettings) -> SourceRegistry:
    registry = load_merged_registry(settings)
    for source in registry.github_repos:
        job_id = f"github:{source.owner}/{source.repo}:commits"
        scheduler.add_job(
            _run_github_job,
            "interval",
            minutes=source.poll_interval_minutes,
            id=job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            args=[scheduler, job_id, source.owner, source.repo, "commits", settings],
        )
    for source in registry.rss_feeds:
        url = str(source.url)
        job_id = f"rss:{url}"
        scheduler.add_job(
            _run_rss_job,
            "interval",
            minutes=source.poll_interval_minutes,
            id=job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            args=[scheduler, job_id, url, source.regex_exclude, settings],
        )
    logger.info(
        "scout_jobs_registered",
        github_jobs=len(registry.github_repos),
        rss_jobs=len(registry.rss_feeds),
        web_page_jobs=len(registry.web_pages),
    )
    return registry
