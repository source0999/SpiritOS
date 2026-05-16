from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class BudgetStatusUnavailable(RuntimeError):
    """Raised when LiteLLM budget status cannot be read."""


@dataclass(frozen=True)
class BudgetStatus:
    user: str
    total_budget: float
    current_cost: float

    @property
    def remaining(self) -> float:
        return max(self.total_budget - self.current_cost, 0.0)

    def as_healthcheck_payload(self) -> dict[str, str]:
        return {"budget_remaining": _format_usd(self.remaining)}


def collect_budget_status() -> BudgetStatus:
    data_dir = Path(os.getenv("SOURCE_PROXY_DATA_DIR", "data/source-proxy"))
    project = os.getenv("SOURCE_PROXY_BUDGET_PROJECT", "source")
    user = os.getenv("SOURCE_PROXY_BUDGET_USER", "source")
    total_budget = _read_total_budget()

    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        from litellm import BudgetManager

        with _working_directory(data_dir):
            manager = BudgetManager(project_name=project, client_type="local")
            if not manager.is_valid_user(user):
                manager.create_budget(total_budget=total_budget, user=user)
                manager.save_data()

            return BudgetStatus(
                user=user,
                total_budget=float(manager.get_total_budget(user)),
                current_cost=float(manager.get_current_cost(user)),
            )
    except Exception as error:
        raise BudgetStatusUnavailable(
            f"Unable to read LiteLLM budget status: {error}"
        ) from error


def _read_total_budget() -> float:
    raw_value = os.getenv("SOURCE_PROXY_BUDGET_TOTAL_USD", "0.00")
    try:
        return float(raw_value)
    except ValueError as error:
        raise BudgetStatusUnavailable(
            f"SOURCE_PROXY_BUDGET_TOTAL_USD must be numeric, got {raw_value!r}."
        ) from error


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _format_usd(value: float) -> str:
    return f"${value:.2f}"
