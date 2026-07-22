from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
)
from source_proxy.target_plugins.generic_workspace import (
    GENERIC_RICH_EXECUTION_PATH,
    _normalize_selected_context_packet,
    _render_scoped_workspace_context,
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


def test_scoped_workspace_context_includes_authorized_untracked_files(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    untracked = root / "src" / "new_helper.py"
    untracked.write_text("VALUE = 'current'\n", encoding="utf-8")

    rendered, manifest = _render_scoped_workspace_context(root, ("src/",))

    assert "--- src/new_helper.py ---\nVALUE = 'current'\n" in rendered
    entry = next(item for item in manifest if item["path"] == "src/new_helper.py")
    assert entry["sha256"] == hashlib.sha256(untracked.read_bytes()).hexdigest()
    assert entry["size"] == len(untracked.read_bytes())


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

    def plan_ready(
        plan: object,
        expanded_context: dict[str, object],
    ) -> dict[str, object]:
        calls.append("plan_ready")
        assert getattr(plan, "task_id") == "production-task-123"
        assert getattr(plan, "coder_packet").target_file.path == "src/service.py"
        assert expanded_context["go_eligible"] is False
        architect_source = next(
            item
            for item in expanded_context["sources_considered"]
            if item["source"] == "architect_repository_context"
        )
        packet = architect_source["packet"]
        assert packet["scoped_workspace_context"].startswith(
            "ADDITIONAL CURRENT AUTHORIZED FILES:\n"
        )
        assert packet["scoped_workspace_context_manifest"]
        assert packet["scoped_workspace_context_sha256"] == hashlib.sha256(
            packet["scoped_workspace_context"].encode("utf-8")
        ).hexdigest()
        assert packet["rendered_coder_context"]
        assert packet["rendered_coder_context_sha256"] == hashlib.sha256(
            packet["rendered_coder_context"].encode("utf-8")
        ).hexdigest()
        return acknowledge_context_consumer(
            expanded_context,
            consumer="planner",
            evidence="test_server_planner_validated_late_bound_context",
            reason="test_server_persisted_exact_architect_plan",
        )

    def coder_ready(
        plan: object,
        persisted_context: dict[str, object],
        rendered_prompt_sha256: str,
    ) -> dict[str, object]:
        calls.append("coder_ready")
        assert getattr(plan, "task_id") == "production-task-123"
        assert len(rendered_prompt_sha256) == 64
        return acknowledge_context_consumer(
            persisted_context,
            consumer="coder",
            evidence="test_adapter_context_bound_before_coder",
            reason="test_coder_consumes_exact_expanded_context",
        )

    result = execute_generic_workspace_rich(
        task="Add a normalize_name service function and focused tests.",
        workspace_root=root,
        allowed_paths=("src/", "tests/"),
        model_call=coder_call,
        architect_model_call=architect_call,
        coder_model_call=coder_call,
        model_alias="coder",
        canonical_context={
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
        },
        architect_task_id="production-task-123",
        plan_ready_callback=plan_ready,
        coder_ready_callback=coder_ready,
    )

    assert result.get("coder_blocked") is not True
    assert result["execution_path"] == GENERIC_RICH_EXECUTION_PATH
    assert calls == ["architect", "plan_ready", "coder_ready", "coder"]
    diagnostics = result["coder_diagnostics"]
    assert any(
        item.get("source") == "refreshed_orchestrator_context"
        for item in diagnostics["canonical_context_broker"]["sources_considered"]
    )
    assert diagnostics["multi_file_capability_requested"] is True
    assert diagnostics["changed_files"] == ["src/service.py", "tests/test_service.py"]
    assert "diff --git a/src/service.py b/src/service.py" in result["proposed_diff"]
    assert "diff --git a/tests/test_service.py b/tests/test_service.py" in result["proposed_diff"]


def test_reused_server_plan_skips_architect_and_dispatches_coder(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    architect_calls = 0
    coder_calls = 0
    captured_plan: list[object] = []
    captured_context: list[dict[str, object]] = []

    def architect_call(_prompt: str, _alias: str) -> str:
        nonlocal architect_calls
        architect_calls += 1
        return _architect_response("src/service.py")

    def coder_call(_prompt: str, _alias: str) -> str:
        nonlocal coder_calls
        coder_calls += 1
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

    def plan_ready(
        plan: object,
        staged_context: dict[str, object],
    ) -> dict[str, object]:
        captured_plan.append(plan)
        return acknowledge_context_consumer(
            staged_context,
            consumer="planner",
            evidence="test_server_validated_reusable_plan",
            reason="test_server_persisted_exact_plan",
        )

    def coder_ready(
        _plan: object,
        planner_context: dict[str, object],
        _rendered_prompt_sha256: str,
    ) -> dict[str, object]:
        acknowledged = acknowledge_context_consumer(
            planner_context,
            consumer="coder",
            evidence="test_coder_bound_to_reusable_plan",
            reason="test_coder_dispatch_boundary",
        )
        captured_context.append(acknowledged)
        return acknowledged

    common = {
        "task": "Add a normalize_name service function and focused tests.",
        "workspace_root": root,
        "allowed_paths": ("src/", "tests/"),
        "model_call": coder_call,
        "architect_model_call": architect_call,
        "coder_model_call": coder_call,
        "model_alias": "coder",
        "architect_task_id": "reused-server-plan-task",
        "coder_ready_callback": coder_ready,
    }
    primary = execute_generic_workspace_rich(
        **common,
        canonical_context={"sources_considered": []},
        plan_ready_callback=plan_ready,
    )
    replacement = execute_generic_workspace_rich(
        **common,
        canonical_context=captured_context[-1],
        prevalidated_plan=captured_plan[-1],
    )

    assert primary.get("coder_blocked") is not True
    assert replacement.get("coder_blocked") is not True
    assert replacement["coder_diagnostics"]["architect_mode"] == (
        "server_persisted_plan_reuse"
    )
    assert architect_calls == 1
    assert coder_calls == 2


@pytest.mark.parametrize("packet_mode", ["omitted", "empty"])
def test_required_empty_task_description_packet_remains_go_eligible(
    tmp_path: Path,
    packet_mode: str,
) -> None:
    root = _workspace(tmp_path)
    returned_context: dict[str, object] = {}
    coder_prompts: list[str] = []

    def architect_call(_prompt: str, _alias: str) -> str:
        return _architect_response("src/service.py")

    def coder_call(prompt: str, _alias: str) -> str:
        coder_prompts.append(prompt)
        assert "selected context packet: http-task-description" not in prompt
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

    def plan_ready(
        _plan: object,
        expanded_context: dict[str, object],
    ) -> dict[str, object]:
        source = next(
            item
            for item in expanded_context["sources_considered"]
            if item["source"] == "http-task-description"
        )
        assert source["required"] is True
        assert source["selected"] is True
        assert source["included"] is True
        assert source["packet"] == {}
        return acknowledge_context_consumer(
            expanded_context,
            consumer="planner",
            evidence="test_server_planner_validated_late_bound_context",
            reason="test_server_persisted_exact_architect_plan",
        )

    def coder_ready(
        _plan: object,
        persisted_context: dict[str, object],
        rendered_prompt_sha256: str,
    ) -> dict[str, object]:
        assert len(rendered_prompt_sha256) == 64
        acknowledged = acknowledge_context_consumer(
            persisted_context,
            consumer="coder",
            evidence="exact_rendered_context_bound_for_test_coder",
            reason="coder_consumes_the_callback_returned_context",
        )
        returned_context.update(acknowledged)
        return acknowledged

    task_source: dict[str, object] = {
        "source": "http-task-description",
        "considered": True,
        "status": "used",
        "reason": "task_text_bound_by_authenticated_request",
        "required": True,
        "selected": True,
        "included": True,
    }
    if packet_mode == "empty":
        task_source["packet"] = {}

    result = execute_generic_workspace_rich(
        task="Add a normalize_name service function and focused tests.",
        workspace_root=root,
        allowed_paths=("src/", "tests/"),
        model_call=coder_call,
        architect_model_call=architect_call,
        coder_model_call=coder_call,
        model_alias="coder",
        canonical_context={"sources_considered": [task_source]},
        architect_task_id="production-empty-packet-task",
        plan_ready_callback=plan_ready,
        coder_ready_callback=coder_ready,
    )

    assert result.get("coder_blocked") is not True
    assert coder_prompts
    diagnostics = result["coder_diagnostics"]
    broker = diagnostics["canonical_context_broker"]
    assert broker == returned_context
    assert diagnostics["canonical_context_report_hash"] == returned_context[
        "canonical_report_hash"
    ]
    http_source = next(
        item
        for item in broker["sources_considered"]
        if item["source"] == "http-task-description"
    )
    assert http_source["packet"] == {}
    assert http_source["consumed"] is True
    assert broker["required_context_blockers"] == []
    assert broker["go_eligible"] is True
    assert set(broker["selected_sources"]) == set(broker["consumed_sources"])
    assert set(broker["downstream_acknowledgements"]["coder"]["sources"]) == set(
        broker["selected_sources"]
    )
    binding = diagnostics["coder_context_binding"]
    assert binding["canonical_context_report_hash"] == broker[
        "canonical_report_hash"
    ]
    assert binding["rendered_prompt_sha256"] == diagnostics[
        "coder_rendered_prompt_sha256"
    ]


def _rebuild_test_context(
    report: dict[str, object],
    *,
    selection_drift: bool = False,
    material_drift: bool = False,
) -> dict[str, object]:
    sources: list[dict[str, object]] = []
    for raw in report["sources_considered"]:
        source = copy.deepcopy(raw)
        source["consumed"] = source.get("consumed_claimed") is True
        if source.get("source") == "optional-request-context":
            if selection_drift:
                source["selected"] = False
                source["included"] = False
                source["included_in_packet"] = False
            if material_drift:
                source["packet"] = {"forged": "replacement"}
        sources.append(source)
    acknowledgements = copy.deepcopy(report["downstream_acknowledgements"])
    if selection_drift:
        selected = [
            str(source.get("source") or "")
            for source in sources
            if source.get("selected") is True and source.get("included") is True
        ]
        for acknowledgement in acknowledgements.values():
            if acknowledgement.get("applicable") is True:
                acknowledgement["sources"] = selected
    return build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=report["applicable_consumers"],
    )


@pytest.mark.parametrize(
    ("failure_case", "expected_reason"),
    [
        (
            "incomplete_pair",
            "generic_workspace_context_callback_pair_incomplete",
        ),
        ("planner_none", "generic_workspace_context_refresh_missing"),
        (
            "planner_material",
            "generic_workspace_refreshed_context_material_mismatch",
        ),
        (
            "planner_selection",
            "generic_workspace_refreshed_context_selection_mismatch",
        ),
        ("coder_none", "generic_workspace_coder_context_refresh_missing"),
        (
            "coder_material",
            "generic_workspace_refreshed_context_material_mismatch",
        ),
        (
            "coder_selection",
            "generic_workspace_refreshed_context_selection_mismatch",
        ),
        (
            "coder_missing_ack",
            "generic_workspace_refreshed_context_coder_acknowledgement_missing",
        ),
    ],
)
def test_context_callbacks_fail_closed_before_provider_dispatch(
    tmp_path: Path,
    failure_case: str,
    expected_reason: str,
) -> None:
    root = _workspace(tmp_path)
    coder_calls = 0

    def architect_call(_prompt: str, _alias: str) -> str:
        return _architect_response("src/service.py")

    def coder_call(_prompt: str, _alias: str) -> str:
        nonlocal coder_calls
        coder_calls += 1
        raise AssertionError("context callback failure must precede provider dispatch")

    def plan_ready(
        _plan: object,
        expanded_context: dict[str, object],
        ) -> dict[str, object] | None:
            if failure_case == "planner_none":
                return None
            acknowledged = acknowledge_context_consumer(
                expanded_context,
                consumer="planner",
                evidence="test_server_planner_validated_late_bound_context",
                reason="test_server_persisted_exact_architect_plan",
            )
            if failure_case == "planner_material":
                return _rebuild_test_context(acknowledged, material_drift=True)
            if failure_case == "planner_selection":
                return _rebuild_test_context(acknowledged, selection_drift=True)
            return acknowledged

    def coder_ready(
        _plan: object,
        persisted_context: dict[str, object],
        _rendered_prompt_sha256: str,
    ) -> dict[str, object] | None:
        if failure_case == "coder_none":
            return None
        if failure_case == "coder_missing_ack":
            return persisted_context
        acknowledged = acknowledge_context_consumer(
            persisted_context,
            consumer="coder",
            evidence="test_coder_context_acknowledged",
            reason="test_provider_dispatch_boundary",
        )
        if failure_case == "coder_material":
            return _rebuild_test_context(acknowledged, material_drift=True)
        if failure_case == "coder_selection":
            return _rebuild_test_context(acknowledged, selection_drift=True)
        return acknowledged

    kwargs: dict[str, object] = {
        "task": "Add a normalize_name service function and focused tests.",
        "workspace_root": root,
        "allowed_paths": ("src/", "tests/"),
        "model_call": coder_call,
        "architect_model_call": architect_call,
        "coder_model_call": coder_call,
        "model_alias": "coder",
        "canonical_context": {
            "sources_considered": [
                {
                    "source": "optional-request-context",
                    "considered": True,
                    "status": "used",
                    "reason": "optional_context_selected",
                    "required": False,
                    "selected": True,
                    "included": True,
                    "packet": {"request": "implement"},
                }
            ]
        },
        "architect_task_id": "context-callback-fail-closed",
        "plan_ready_callback": plan_ready,
    }
    if failure_case != "incomplete_pair":
        kwargs["coder_ready_callback"] = coder_ready

    result = execute_generic_workspace_rich(**kwargs)

    assert result["coder_blocked"] is True
    assert result["reason_code"] == expected_reason
    assert coder_calls == 0


def test_non_derived_reserved_architect_source_cannot_be_replaced(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    coder_calls = 0

    def coder_call(_prompt: str, _alias: str) -> str:
        nonlocal coder_calls
        coder_calls += 1
        raise AssertionError("reserved-source collision must block before Coder")

    result = execute_generic_workspace_rich(
        task="Add a normalize_name service function and focused tests.",
        workspace_root=root,
        allowed_paths=("src/", "tests/"),
        model_call=coder_call,
        architect_model_call=lambda _prompt, _alias: _architect_response(
            "src/service.py"
        ),
        coder_model_call=coder_call,
        model_alias="coder",
        canonical_context={
            "sources_considered": [
                {
                    "source": "architect_repository_context",
                    "considered": True,
                    "status": "used",
                    "reason": "untrusted_reserved_name_claim",
                    "required": False,
                    "selected": True,
                    "included": True,
                    "packet": {"untrusted": True},
                    "authority": {},
                }
            ]
        },
    )

    assert result["coder_blocked"] is True
    assert result["reason_code"] == "generic_workspace_context_not_go_eligible"
    assert any(
        blocker == "duplicate_context_source:architect_repository_context"
        for blocker in result["coder_diagnostics"]["canonical_context_broker"][
            "required_context_blockers"
        ]
    )
    assert coder_calls == 0


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


def test_selected_context_packet_envelope_is_bounded_and_idempotent() -> None:
    packet = {"context": "x" * 5_000, "source": "authenticated-request"}
    packet_json = json.dumps(packet, sort_keys=True, separators=(",", ":"))

    normalized = _normalize_selected_context_packet(packet)

    assert set(normalized) == {
        "schema_version",
        "bounded_context",
        "packet_sha256",
        "bounded_context_sha256",
        "truncated",
    }
    assert normalized["schema_version"] == "source-proxy-bounded-context-packet/v1"
    assert normalized["bounded_context"] == packet_json[:4_000]
    assert normalized["packet_sha256"] == hashlib.sha256(
        packet_json.encode("utf-8")
    ).hexdigest()
    assert normalized["bounded_context_sha256"] == hashlib.sha256(
        packet_json[:4_000].encode("utf-8")
    ).hexdigest()
    assert normalized["truncated"] is True
    assert _normalize_selected_context_packet(normalized) == normalized


def test_untruncated_selected_context_packet_binds_the_full_packet_hash() -> None:
    packet = {"fresh": True, "task": "implement"}
    packet_json = json.dumps(packet, sort_keys=True, separators=(",", ":"))

    normalized = _normalize_selected_context_packet(packet)

    expected_hash = hashlib.sha256(packet_json.encode("utf-8")).hexdigest()
    assert normalized["bounded_context"] == packet_json
    assert normalized["packet_sha256"] == expected_hash
    assert normalized["bounded_context_sha256"] == expected_hash
    assert normalized["truncated"] is False
    assert _normalize_selected_context_packet(normalized) == normalized


@pytest.mark.parametrize(
    "malformation",
    [
        "extra_key",
        "missing_bounded_hash",
        "invalid_bounded_hash",
        "invalid_packet_hash",
        "false_truncation_hash_mismatch",
        "short_truncated_excerpt",
    ],
)
def test_malformed_selected_context_envelope_is_safely_rewrapped(
    malformation: str,
) -> None:
    envelope = _normalize_selected_context_packet({"fresh": True})
    malformed = dict(envelope)
    if malformation == "extra_key":
        malformed["untrusted"] = True
    elif malformation == "missing_bounded_hash":
        malformed.pop("bounded_context_sha256")
    elif malformation == "invalid_bounded_hash":
        malformed["bounded_context_sha256"] = "0" * 64
    elif malformation == "invalid_packet_hash":
        malformed["packet_sha256"] = "not-a-sha256"
    elif malformation == "false_truncation_hash_mismatch":
        malformed["packet_sha256"] = "0" * 64
    elif malformation == "short_truncated_excerpt":
        malformed["truncated"] = True

    malformed_json = json.dumps(
        malformed,
        sort_keys=True,
        separators=(",", ":"),
    )
    normalized = _normalize_selected_context_packet(malformed)

    assert normalized != malformed
    assert normalized["bounded_context"] == malformed_json
    assert normalized["packet_sha256"] == hashlib.sha256(
        malformed_json.encode("utf-8")
    ).hexdigest()
    assert normalized["bounded_context_sha256"] == normalized["packet_sha256"]
    assert normalized["truncated"] is False
    assert _normalize_selected_context_packet(normalized) == normalized
