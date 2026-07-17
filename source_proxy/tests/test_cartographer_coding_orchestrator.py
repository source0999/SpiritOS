from __future__ import annotations

import source_proxy.coding.orchestrator as orchestrator_module
from source_proxy.coding.orchestrator import CodingOrchestrator


def test_cartographer_selection_is_consumed_before_coding_run(monkeypatch) -> None:
    consumed: list[dict[str, str]] = []
    monkeypatch.setattr(
        orchestrator_module,
        "consume_cartographer_selection",
        lambda **kwargs: consumed.append(kwargs) or {"approval_id": kwargs["approval_id"]},
    )
    monkeypatch.setattr(CodingOrchestrator, "start", lambda self, task_id, *, sources: {"task_id": task_id})

    receipt = CodingOrchestrator().start_from_cartographer_selection(
        "task-1", selection_approval_id="apr-selection", proposal_id="proposal-1",
        target="src/example.ts", sources=[],
    )

    assert consumed == [{"approval_id": "apr-selection", "proposal_id": "proposal-1", "consumer": "coding-executor:coder", "target": "src/example.ts"}]
    assert receipt["cartographer_selection"]["approval_id"] == "apr-selection"
