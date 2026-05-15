from __future__ import annotations

from typing import Any, Callable


PlanMigrator = Callable[[dict[str, Any]], dict[str, Any]]

PLAN_MIGRATORS: dict[int, PlanMigrator] = {}
