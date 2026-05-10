from fastapi import FastAPI

from source_proxy import __version__
from source_proxy.api.action_preview import router as action_preview_router
from source_proxy.api.chat import router as chat_router
from source_proxy.api.context_index import router as context_index_router
from source_proxy.api.context_inventory import router as context_inventory_router
from source_proxy.api.decision import router as decision_router
from source_proxy.api.healthcheck import router as healthcheck_router
from source_proxy.api.self_status import router as self_status_router
from source_proxy.api.tools_manifest import router as tools_manifest_router
from source_proxy.expenditure.logger import initialize_expenditure_store

app = FastAPI(title="Source Proxy", version=__version__)
app.include_router(action_preview_router)
app.include_router(chat_router)
app.include_router(context_index_router)
app.include_router(context_inventory_router)
app.include_router(decision_router)
app.include_router(healthcheck_router)
app.include_router(self_status_router)
app.include_router(tools_manifest_router)


@app.on_event("startup")
async def startup() -> None:
    await initialize_expenditure_store()


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "source-proxy", "status": "bootstrapped"}
