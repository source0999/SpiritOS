from fastapi import FastAPI

from source_proxy import __version__
from source_proxy.api.action_preview import router as action_preview_router
from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.api.chat import router as chat_router
from source_proxy.api.codex_adapter import router as codex_adapter_router
from source_proxy.api.coding_self_tests import router as coding_self_tests_router
from source_proxy.api.coding_observability import router as coding_observability_router
from source_proxy.api.campaign_3_readiness import router as campaign_3_readiness_router
from source_proxy.api.context_index import router as context_index_router
from source_proxy.api.context_inventory import router as context_inventory_router
from source_proxy.api.decision import router as decision_router
from source_proxy.api.diff_verification import router as diff_verification_router
from source_proxy.api.healthcheck import router as healthcheck_router
from source_proxy.api.long_running_tasks import router as long_running_tasks_router
from source_proxy.api.obsidian_context import router as obsidian_context_router
from source_proxy.api.runtime_status import router as runtime_status_router
from source_proxy.api.self_status import router as self_status_router
from source_proxy.api.sandbox_terminal import router as sandbox_terminal_router
from source_proxy.api.scout_intake import router as scout_intake_router
from source_proxy.api.tools_manifest import router as tools_manifest_router
from source_proxy.api.workspace_tools import router as workspace_tools_router
from source_proxy.expenditure.logger import initialize_expenditure_store

app = FastAPI(title="Source Proxy", version=__version__)
# Human-approved local diffs: execution goes to POST /v1/tasks/long-running/{id}/execute-approved
# (see approval.gate). Diff preview sets limits.file_writes_allowed for local_route only
# (see verification.diff); the preview endpoint never writes — apply happens only after approval.
app.state.coder_agent_execution = {
    "approved_workspace_writes_enabled": True,
    "execute_approved_endpoint": "/v1/tasks/long-running/{task_id}/execute-approved",
    "workspace_root_resolution": "SPIRIT_PROJECT_PATH + SOURCE_PROXY_PROJECT_ROOTS: first existing comma-separated roots; git apply tries each then package.json walk (see long_running._ordered_workspace_roots_for_apply)",
}
app.include_router(action_preview_router)
app.include_router(cartographer_router)
app.include_router(chat_router)
app.include_router(codex_adapter_router)
app.include_router(coding_self_tests_router)
app.include_router(coding_observability_router)
app.include_router(campaign_3_readiness_router)
app.include_router(context_index_router)
app.include_router(context_inventory_router)
app.include_router(decision_router)
app.include_router(diff_verification_router)
app.include_router(healthcheck_router)
app.include_router(long_running_tasks_router)
app.include_router(obsidian_context_router)
app.include_router(runtime_status_router)
app.include_router(sandbox_terminal_router)
app.include_router(scout_intake_router)
app.include_router(self_status_router)
app.include_router(tools_manifest_router)
app.include_router(workspace_tools_router)


@app.on_event("startup")
async def startup() -> None:
    await initialize_expenditure_store()
    # Execution policy is declared on app.state at import time; startup is the hook
    # if we later need to flip flags from env. For now the struct is documentation + future wiring.


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "service": "source-proxy",
        "status": "bootstrapped",
        "write_policy": {
            "apply_requires_approval": True,
            "commit_requires_separate_approval": True,
            "push_requires_separate_approval": True,
        },
    }
