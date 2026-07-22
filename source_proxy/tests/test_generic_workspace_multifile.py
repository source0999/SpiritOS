from __future__ import annotations

import json
import subprocess
from pathlib import Path

from source_proxy.target_plugins.generic_workspace import (
    GENERIC_RICH_EXECUTION_PATH,
    execute_generic_workspace_rich,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _architect_response(target: str) -> str:
    return json.dumps(
        {
            "classification": {
                "task_class": "implement",
                "visual_change": False,
                "designer_required": False,
                "estimated_complexity": "small",
            },
            "coder_packet": {
                "target_file": {"path": target, "exists": True},
                "operation": "edit",
                "acceptance_criteria": [
                    {
                        "id": "service-and-tests",
                        "description": "Add the requested service function and focused tests.",
                        "kind": "behavioral",
                    }
                ],
                "constraints": {},
                "context_slices": [],
                "forbidden_paths": [],
                "style_directives": [],
            },
        }
    )


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "service.py").write_text(
        "def existing() -> str:\n    return 'kept'\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_service.py").write_text(
        "from src.service import existing\n\n\ndef test_existing():\n    assert existing() == 'kept'\n",
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "baseline")
    return root


def test_rich_path_builds_one_atomic_multi_file_diff(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    calls: list[str] = []

    def architect_call(prompt: str, _alias: str) -> str:
        calls.append("architect")
        assert "Workspace file index" in prompt
        return _architect_response("src/service.py")

    def coder_call(prompt: str, _alias: str) -> str:
        calls.append("coder")
        assert "Architect-owned multi-file packet" in prompt
        assert "src/service.py" in prompt
        assert "tests/test_service.py" in prompt
        return json.dumps(
            {
                "files": [
                    {
                        "path": "src/service.py",
                        "content": (
                            "def existing() -> str:\n"
                            "    return 'kept'\n\n\n"
                            "def normalize_name(value: str) -> str:\n"
                            "    return value.strip().lower()\n"
                        ),
                    },
                    {
                        "path": "tests/test_service.py",
                        "content": (
                            "from src.service import existing, normalize_name\n\n\n"
                            "def test_existing():\n"
                            "    assert existing() == 'kept'\n\n\n"
                            "def test_normalize_name():\n"
                            "    assert normalize_name('  ALICE ') == 'alice'\n"
                        ),
                    },
                ]
            }
        )

    def plan_ready(plan: object) -> dict[str, object]:
        calls.append("plan_ready")
        assert getattr(plan, "task_id") == "production-task-123"
        assert getattr(plan, "coder_packet").target_file.path == "src/service.py"
        return {
            "sources_considered": [
                {
                    "source": "refreshed_orchestrator_context",
                    "considered": True,
                    "status": "used",
                    "required": True,
                    "selected": True,
                    "included": True,
                    "packet": {"fresh": True},
                }
            ]
        }

    result = execute_generic_workspace_rich(
        task="Add a normalize_name service function and focused tests.",
        workspace_root=root,
        allowed_paths=("src/", "tests/"),
        model_call=coder_call,
        architect_model_call=architect_call,
        coder_model_call=coder_call,
        model_alias="coder",
        canonical_context={},
        architect_task_id="production-task-123",
        plan_ready_callback=plan_ready,
    )

    assert result.get("coder_blocked") is not True
    assert result["execution_path"] == GENERIC_RICH_EXECUTION_PATH
    assert calls == ["architect", "plan_ready", "coder"]
    diagnostics = result["coder_diagnostics"]
    assert any(
        item.get("source") == "refreshed_orchestrator_context"
        for item in diagnostics["canonical_context_broker"]["sources_considered"]
    )
    assert diagnostics["multi_file_capability_requested"] is True
    assert diagnostics["changed_files"] == ["src/service.py", "tests/test_service.py"]
    assert "diff --git a/src/service.py b/src/service.py" in result["proposed_diff"]
    assert "diff --git a/tests/test_service.py b/tests/test_service.py" in result["proposed_diff"]


def test_multi_file_packet_rejects_one_out_of_scope_member(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    def architect_call(_prompt: str, _alias: str) -> str:
        return _architect_response("src/service.py")

    def coder_call(_prompt: str, _alias: str) -> str:
        return json.dumps(
            {
                "files": [
                    {"path": "src/service.py", "content": "VALUE = 1\n"},
                    {"path": "private/answer.py", "content": "ANSWER = True\n"},
                ]
            }
        )

    result = execute_generic_workspace_rich(
        task="Add a service function and tests in the authorized source tree.",
        workspace_root=root,
        allowed_paths=("src/", "tests/"),
        model_call=coder_call,
        architect_model_call=architect_call,
        coder_model_call=coder_call,
        model_alias="coder",
        canonical_context={},
    )

    assert result["coder_blocked"] is True
    assert result["proposed_diff"] == ""
    assert not (root / "private").exists()
