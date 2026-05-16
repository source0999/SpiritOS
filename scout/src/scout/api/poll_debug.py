from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scout.config import get_settings
from scout.pollers.github import poll_repo
from scout.pollers.registry import load_registry
from scout.pollers.rss import poll_feed

router = APIRouter(prefix="/v1/scout/_debug")


class DebugPollRequest(BaseModel):
    kind: Literal["github", "rss"]
    owner: str | None = None
    repo: str | None = None
    endpoint: str = "commits"
    url: str | None = None


@router.post("/poll")
async def debug_poll(request: DebugPollRequest) -> dict:
    settings = get_settings()
    if not settings.debug_poll_enabled:
        raise HTTPException(status_code=404, detail="debug polling is disabled")

    registry = load_registry(settings.config_path)
    if request.kind == "github":
        if not request.owner or not request.repo:
            raise HTTPException(status_code=422, detail="owner and repo are required")
        allowed = any(
            source.owner == request.owner and source.repo == request.repo
            for source in registry.github_repos
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="source is not allowlisted")
        result = await poll_repo(
            request.owner,
            request.repo,
            request.endpoint,
            settings=settings,
        )
        return result.__dict__

    if not request.url:
        raise HTTPException(status_code=422, detail="url is required")
    allowed_feed = next(
        (source for source in registry.rss_feeds if str(source.url) == request.url),
        None,
    )
    if not allowed_feed:
        raise HTTPException(status_code=403, detail="source is not allowlisted")
    result = await poll_feed(
        request.url,
        regex_exclude=allowed_feed.regex_exclude,
        settings=settings,
    )
    return result.__dict__
