from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
import structlog

from scout.api.health import router as health_router
from scout.api.overview import router as overview_router
from scout.api.packets import router as packets_router
from scout.api.poll_debug import router as poll_debug_router
from scout.api.promotions import router as promotions_router
from scout.config import get_settings
from scout.debugger.runner import register_debugger_job
from scout.extractors import register_extractor_job
from scout.packets.orchestrator import register_synthesis_job
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations
from scout.storage.pruning import register_pruning_job
from scout.pollers.registry import register_jobs

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()

scheduler = AsyncIOScheduler()

from scout.api.status import router as status_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("scout_starting", db_path=str(settings.database_path))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "logs").mkdir(exist_ok=True)
    (settings.data_dir / "cache").mkdir(exist_ok=True)
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    register_jobs(scheduler, settings)
    register_extractor_job(scheduler, settings)
    register_synthesis_job(scheduler, settings)
    register_debugger_job(scheduler, settings)
    register_pruning_job(scheduler, settings)
    scheduler.start()
    try:
        yield
    finally:
        logger.info("scout_stopping")
        scheduler.shutdown(wait=False)


app = FastAPI(title="Scout v0.1", lifespan=lifespan)
app.include_router(health_router)
app.include_router(status_router)
app.include_router(overview_router)
app.include_router(poll_debug_router)
app.include_router(packets_router)
app.include_router(promotions_router)
