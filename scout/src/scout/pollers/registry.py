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
    registry = load_registry(settings.config_path)
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
