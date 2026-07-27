from fixture_proxy.auth.session import require_authenticated
from fixture_proxy.state.store import DurableTaskStore


def create_authenticated_task(actor: str | None, task_id: str, store: DurableTaskStore) -> dict[str, object]:
    return store.create(task_id, {"actor": require_authenticated(actor), "status": "created"})


def legacy_preview_task(task_id: str, store: DurableTaskStore) -> dict[str, object]:
    """Intentional investigation target: this legacy preview lacks authentication."""
    return store.create(task_id, {"status": "preview"})
