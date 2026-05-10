from fastapi import FastAPI

from source_proxy import __version__
from source_proxy.api.chat import router as chat_router
from source_proxy.api.decision import router as decision_router
from source_proxy.api.healthcheck import router as healthcheck_router
from source_proxy.expenditure.logger import initialize_expenditure_store

app = FastAPI(title="Source Proxy", version=__version__)
app.include_router(chat_router)
app.include_router(decision_router)
app.include_router(healthcheck_router)


@app.on_event("startup")
async def startup() -> None:
    await initialize_expenditure_store()


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "source-proxy", "status": "bootstrapped"}
