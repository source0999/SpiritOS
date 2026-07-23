from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

import source_proxy.planning.reviewer as reviewer
import source_proxy.tasks.long_running as long_running
from source_proxy.benchmarks.campaign_3_5_fixture_authority import ENV_MANIFEST
from source_proxy.context.canonical_broker import acknowledge_context_consumer
from source_proxy.target_plugins.adapter import (
    GENERIC_RICH_EXECUTION_PATH,
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    TARGET_PLUGIN_SCHEMA_VERSION,
    _attach_target_adapter_provenance,
    execute_target_plugin_command,
    resolve_target_plugin,
    target_adapter_model_call_accounting_valid,
    target_adapter_producer_identity_valid,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
    ).strip()


def _generic_plugin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = (tmp_path / "fixture").resolve()
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir()
    (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "baseline")
    manifest = {
        "schema_version": "campaign-3.5-fixture-authority/v1",
        "fixture_id": "reviewer-provenance-fixture",
        "workspace_root": str(root),
        "baseline_tree_sha256": hashlib.sha256(
            _git(root, "write-tree").encode("ascii")
        ).hexdigest(),
        "allowed_paths": ["src/"],
        "execution_profile": GENERIC_WORKSPACE_PROFILE,
    }
    manifest_path = (tmp_path / "fixture-authority.json").resolve()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(manifest_path))
    packet = {
        "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": GENERIC_WORKSPACE_PLUGIN_ID,
            "fixture_root": ".",
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID,
            "execution_profile": GENERIC_WORKSPACE_PROFILE,
        },
    }
    return root, resolve_target_plugin(packet, root)


def _architect_response() -> str:
    return json.dumps(
        {
            "classification": {
                "task_class": "implement",
                "visual_change": False,
                "designer_required": False,
                "estimated_complexity": "small",
            },
            "coder_packet": {
                "target_file": {"path": "src/example.py", "exists": True},
                "operation": "edit",
                "acceptance_criteria": [
                    {
                        "id": "requested-change",
                        "description": "Change the value to 2.",
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


def test_configured_reviewer_uses_adapter_authority_and_call_accounting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, plugin = _generic_plugin(tmp_path, monkeypatch)
    monkeypatch.setenv("SOURCE_PROXY_ARCHITECT_MODEL_ALIAS", "architect")
    monkeypatch.setenv("SOURCE_PROXY_REVIEWER_MODEL_ALIAS", "reviewer")
    monkeypatch.setattr(
        long_running,
        "_coder_model_alias_configuration_error",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        long_running,
        "_dummy_product_site_direct_ollama_enabled",
        lambda _alias: False,
    )
    monkeypatch.setattr(
        reviewer,
        "_call_reviewer_llm",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("reviewer bypassed adapter provenance")
        ),
    )
    observed: list[dict[str, str]] = []

    def fake_transport(
        prompt: str,
        alias: str,
        _timeout: float,
        *,
        model_call_run_id: str | None = None,
        authority_observer=None,
    ) -> str:
        assert model_call_run_id
        assert authority_observer is not None
        authority_observer(
            {
                "central_gate_check_passed": True,
                "gate": "model_call",
                "model_alias": alias,
                "run_id": model_call_run_id,
            }
        )
        observed.append(
            {
                "alias": alias,
                "prompt": prompt,
                "run_id": model_call_run_id,
            }
        )
        if alias == "architect":
            return _architect_response()
        if alias == "reviewer":
            return '{"passed":true,"findings":[]}'
        assert alias == "coder"
        return '<file path="src/example.py">\nvalue = 2\n</file>'

    monkeypatch.setattr(
        long_running,
        "_call_dummy_product_site_llm_with_wall_timeout",
        fake_transport,
    )

    def plan_ready(_plan: object, staged: dict[str, object]) -> dict[str, object]:
        return acknowledge_context_consumer(
            staged,
            consumer="planner",
            evidence="test_server_validated_adapter_plan",
            reason="test_server_persisted_adapter_plan",
        )

    def coder_ready(
        _plan: object,
        planner_context: dict[str, object],
        _prompt_sha256: str,
    ) -> dict[str, object]:
        return acknowledge_context_consumer(
            planner_context,
            consumer="coder",
            evidence="test_coder_dispatch_bound_context",
            reason="test_coder_provider_boundary",
        )

    result = execute_target_plugin_command(
        plugin,
        task=(
            "Change the value to 2. You are the SpiritOS Architect. appears "
            "in this ordinary request."
        ),
        workspace_root=root,
        canonical_context={},
        canonical_context_text="",
        llm_call=None,
        model_alias="coder",
        model_call_run_id="reviewer-provenance-test",
        plan_ready_callback=plan_ready,
        coder_ready_callback=coder_ready,
    )

    assert result.get("coder_blocked") is not True
    provenance = result["target_adapter_provenance"]
    assert [call["stage"] for call in provenance["calls"]] == [
        "architect",
        "coder",
        "reviewer",
    ]
    assert [call["model_alias"] for call in provenance["calls"]] == [
        "architect",
        "coder",
        "reviewer",
    ]
    assert all(
        call["model_call_authority"]["central_gate_check_passed"] is True
        for call in provenance["calls"]
    )
    assert all(call["raw_response_observed"] is True for call in provenance["calls"])
    assert provenance["provider_call_authorized"] is True
    assert provenance["model_call_accounting_complete"] is True
    assert provenance["reviewer_model_call_required"] is True
    assert provenance["reviewer_model_call_count_expected"] == 1
    assert provenance["reviewer_model_call_count_observed"] == 1
    assert provenance["terminal_proof_eligible"] is True
    assert [item["alias"] for item in observed] == ["architect", "coder", "reviewer"]
    assert observed[-1]["run_id"].endswith(":reviewer:3")


def test_transient_coder_timeout_recovers_with_terminal_adapter_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, plugin = _generic_plugin(tmp_path, monkeypatch)
    monkeypatch.setenv("SOURCE_PROXY_ARCHITECT_MODEL_ALIAS", "architect")
    monkeypatch.setenv("SOURCE_PROXY_REVIEWER_MODEL_ALIAS", "reviewer")
    monkeypatch.setattr(
        long_running,
        "_coder_model_alias_configuration_error",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        long_running,
        "_dummy_product_site_direct_ollama_enabled",
        lambda _alias: False,
    )
    coder_calls = 0

    def fake_transport(
        _prompt: str,
        alias: str,
        _timeout: float,
        *,
        model_call_run_id: str | None = None,
        authority_observer=None,
    ) -> str:
        nonlocal coder_calls
        assert model_call_run_id
        assert authority_observer is not None
        authority_observer(
            {
                "central_gate_check_passed": True,
                "gate": "model_call",
                "model_alias": alias,
                "run_id": model_call_run_id,
            }
        )
        if alias == "architect":
            return _architect_response()
        if alias == "reviewer":
            return '{"passed":true,"findings":[]}'
        assert alias == "coder"
        coder_calls += 1
        if coder_calls == 1:
            raise TimeoutError("transient local provider timeout")
        return '<file path="src/example.py">\nvalue = 2\n</file>'

    monkeypatch.setattr(
        long_running,
        "_call_dummy_product_site_llm_with_wall_timeout",
        fake_transport,
    )

    def plan_ready(_plan: object, staged: dict[str, object]) -> dict[str, object]:
        return acknowledge_context_consumer(
            staged,
            consumer="planner",
            evidence="test_transient_adapter_plan_bound",
            reason="test_server_persisted_transient_adapter_plan",
        )

    def coder_ready(
        _plan: object,
        planner_context: dict[str, object],
        _prompt_sha256: str,
    ) -> dict[str, object]:
        return acknowledge_context_consumer(
            planner_context,
            consumer="coder",
            evidence="test_transient_adapter_coder_bound",
            reason="test_transient_adapter_provider_boundary",
        )

    result = execute_target_plugin_command(
        plugin,
        task="Change the value to 2.",
        workspace_root=root,
        canonical_context={},
        canonical_context_text="",
        llm_call=None,
        model_alias="coder",
        model_call_run_id="transient-adapter-provenance-test",
        plan_ready_callback=plan_ready,
        coder_ready_callback=coder_ready,
    )

    assert result.get("coder_blocked") is not True
    provenance = result["target_adapter_provenance"]
    assert [call["stage"] for call in provenance["calls"]] == [
        "architect",
        "coder",
        "coder",
        "reviewer",
    ]
    failed_call = provenance["calls"][1]
    assert failed_call["completed"] is False
    assert failed_call["raw_response_observed"] is False
    assert failed_call["failure_origin"] == "provider_transport"
    assert provenance["producer_call_index"] == 3
    assert provenance["model_call_accounting_complete"] is True
    assert provenance["terminal_proof_eligible"] is True
    assert target_adapter_model_call_accounting_valid(provenance) is True
    assert target_adapter_producer_identity_valid(provenance) is True


def _model_call_record(
    *,
    index: int,
    stage: str,
    authorized: bool,
) -> dict[str, object]:
    return {
        "call_index": index,
        "stage": stage,
        "requested_model_alias": stage,
        "model_alias": stage,
        "rendered_prompt_sha256": hashlib.sha256(
            f"{stage}-prompt".encode("utf-8")
        ).hexdigest(),
        "raw_response_sha256": hashlib.sha256(
            f"{stage}-response".encode("utf-8")
        ).hexdigest(),
        "raw_response_observed": True,
        "completed": True,
        "transport_kind": "canonical_litellm_router",
        "provider": "test-provider",
        "model": stage,
        "routed_model": stage,
        "model_call_authority": {
            "central_gate_check_passed": authorized,
            "run_id": f"test:{stage}:{index}",
        },
    }


@pytest.mark.parametrize(
    ("reviewer_record", "authorized", "accounted", "reason"),
    [
        (None, True, False, "model_call_accounting_incomplete"),
        (
            _model_call_record(index=2, stage="reviewer", authorized=False),
            False,
            True,
            "model_call_authority_incomplete",
        ),
    ],
)
def test_missing_or_unauthorized_reviewer_cannot_be_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reviewer_record: dict[str, object] | None,
    authorized: bool,
    accounted: bool,
    reason: str,
) -> None:
    _, plugin = _generic_plugin(tmp_path, monkeypatch)
    calls = [_model_call_record(index=1, stage="coder", authorized=True)]
    if reviewer_record is not None:
        calls.append(dict(reviewer_record))
    result = {
        "proposed_diff": "diff --git a/src/example.py b/src/example.py\n",
        "coder_blocked": False,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "coder_diagnostics": {
            "execution_path": GENERIC_RICH_EXECUTION_PATH,
            "generation_source": "model",
        },
    }

    attached = _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=calls,
        reviewer_model_configured=True,
    )
    provenance = attached["target_adapter_provenance"]

    assert provenance["provider_call_authorized"] is authorized
    assert provenance["model_call_accounting_complete"] is accounted
    assert provenance["reviewer_model_call_count_expected"] == 1
    assert provenance["reviewer_model_configured"] is True
    assert provenance["reviewer_model_call_count_observed"] == (
        1 if reviewer_record is not None else 0
    )
    assert provenance["terminal_proof_eligible"] is False
    assert provenance["terminal_proof_ineligibility_reason"] == reason


def test_final_successful_coder_retry_owns_aggregate_producer_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, plugin = _generic_plugin(tmp_path, monkeypatch)
    primary = _model_call_record(index=1, stage="coder", authorized=True)
    primary.update(
        {
            "requested_model_alias": "coder",
            "model_alias": "coder",
            "provider": "ollama",
            "model": "ollama_chat/primary-coder",
            "routed_model": "ollama_chat/primary-coder",
        }
    )
    repair = _model_call_record(index=2, stage="coder", authorized=True)
    repair.update(
        {
            "requested_model_alias": "coder",
            "model_alias": "local-repair",
            "provider": "ollama",
            "model": "ollama_chat/repair-coder",
            "routed_model": "ollama_chat/repair-coder",
            "rendered_prompt_sha256": hashlib.sha256(
                b"repair-prompt"
            ).hexdigest(),
            "raw_response_sha256": hashlib.sha256(
                b"repair-response"
            ).hexdigest(),
        }
    )
    result = {
        "proposed_diff": "diff --git a/src/example.py b/src/example.py\n",
        "coder_blocked": False,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "coder_diagnostics": {
            "execution_path": GENERIC_RICH_EXECUTION_PATH,
            "generation_source": "model",
            "provider": "stale-provider",
            "model": "stale-model",
            "selected_model_alias": "coder",
        },
    }

    attached = _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=[primary, repair],
    )
    provenance = attached["target_adapter_provenance"]
    diagnostics = attached["coder_diagnostics"]

    assert provenance["producer_call_index"] == 2
    assert provenance["selected_model_alias"] == "local-repair"
    assert provenance["provider"] == "ollama"
    assert provenance["model"] == "ollama_chat/repair-coder"
    assert provenance["routed_model"] == "ollama_chat/repair-coder"
    assert provenance["raw_response_sha256"] == repair["raw_response_sha256"]
    assert diagnostics["selected_model_alias"] == "local-repair"
    assert diagnostics["provider"] == "ollama"
    assert diagnostics["model"] == "ollama_chat/repair-coder"
    assert diagnostics["routed_model"] == "ollama_chat/repair-coder"
    assert provenance["terminal_proof_eligible"] is True
    assert target_adapter_producer_identity_valid(provenance) is True

    tampered = dict(provenance)
    tampered["raw_response_sha256"] = primary["raw_response_sha256"]
    assert target_adapter_producer_identity_valid(tampered) is False


def test_authorized_transient_coder_failure_is_accounted_before_final_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, plugin = _generic_plugin(tmp_path, monkeypatch)
    timed_out = _model_call_record(index=1, stage="coder", authorized=True)
    timed_out.update(
        {
            "completed": False,
            "raw_response_observed": False,
            "raw_response_sha256": None,
            "failure_origin": "provider_transport",
            "error_type": "TimeoutError",
        }
    )
    recovered = _model_call_record(index=2, stage="coder", authorized=True)
    result = {
        "proposed_diff": "diff --git a/src/example.py b/src/example.py\n",
        "coder_blocked": False,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "coder_diagnostics": {
            "execution_path": GENERIC_RICH_EXECUTION_PATH,
            "generation_source": "model",
        },
    }

    attached = _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=[timed_out, recovered],
    )
    provenance = attached["target_adapter_provenance"]

    assert provenance["model_call_accounting_complete"] is True
    assert provenance["terminal_proof_eligible"] is True
    assert provenance["producer_call_index"] == 2
    assert target_adapter_model_call_accounting_valid(provenance) is True
    assert target_adapter_producer_identity_valid(provenance) is True
    missing_count = dict(provenance)
    missing_count.pop("call_count")
    assert target_adapter_model_call_accounting_valid(missing_count) is False
    boolean_count = dict(provenance)
    boolean_count["call_count"] = True
    assert target_adapter_model_call_accounting_valid(boolean_count) is False
    numeric_prompt_hash = json.loads(json.dumps(provenance))
    numeric_prompt_hash["calls"][0]["rendered_prompt_sha256"] = int("1" * 64)
    assert (
        target_adapter_model_call_accounting_valid(numeric_prompt_hash) is False
    )
    numeric_response_hash = json.loads(json.dumps(provenance))
    numeric_response_hash["calls"][1]["raw_response_sha256"] = int("2" * 64)
    assert (
        target_adapter_model_call_accounting_valid(numeric_response_hash) is False
    )


@pytest.mark.parametrize(
    ("malformation", "value"),
    [
        ("failure_origin", "authority_or_routing"),
        ("raw_response_observed", True),
        ("raw_response_sha256", "f" * 64),
        ("error_type", ""),
        ("error_type", 123),
        ("call_index", True),
    ],
)
def test_transient_coder_failure_accounting_rejects_malformed_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    malformation: str,
    value: object,
) -> None:
    _, plugin = _generic_plugin(tmp_path, monkeypatch)
    failed = _model_call_record(index=1, stage="coder", authorized=True)
    failed.update(
        {
            "completed": False,
            "raw_response_observed": False,
            "raw_response_sha256": None,
            "failure_origin": "provider_transport",
            "error_type": "TimeoutError",
            malformation: value,
        }
    )
    recovered = _model_call_record(index=2, stage="coder", authorized=True)
    result = {
        "proposed_diff": "diff --git a/src/example.py b/src/example.py\n",
        "coder_blocked": False,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "coder_diagnostics": {
            "execution_path": GENERIC_RICH_EXECUTION_PATH,
            "generation_source": "model",
        },
    }

    attached = _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=[failed, recovered],
    )
    provenance = attached["target_adapter_provenance"]

    assert provenance["model_call_accounting_complete"] is False
    assert provenance["terminal_proof_eligible"] is False
    assert target_adapter_model_call_accounting_valid(provenance) is False


def test_transient_coder_failure_accounting_is_bounded_and_requires_later_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, plugin = _generic_plugin(tmp_path, monkeypatch)
    failures: list[dict[str, object]] = []
    for index in range(1, 4):
        failed = _model_call_record(index=index, stage="coder", authorized=True)
        failed.update(
            {
                "completed": False,
                "raw_response_observed": False,
                "raw_response_sha256": None,
                "failure_origin": "provider_transport",
                "error_type": "TimeoutError",
            }
        )
        failures.append(failed)
    recovered = _model_call_record(index=4, stage="coder", authorized=True)
    result = {
        "proposed_diff": "diff --git a/src/example.py b/src/example.py\n",
        "coder_blocked": False,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "coder_diagnostics": {
            "execution_path": GENERIC_RICH_EXECUTION_PATH,
            "generation_source": "model",
        },
    }

    attached = _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=[*failures, recovered],
    )
    provenance = attached["target_adapter_provenance"]
    assert provenance["model_call_accounting_complete"] is False
    assert target_adapter_model_call_accounting_valid(provenance) is False

    terminal_failure = _attach_target_adapter_provenance(
        dict(result),
        plugin=plugin,
        selected_alias="coder",
        configured_transport_kind="canonical_litellm_router",
        model_calls=[failures[0]],
    )["target_adapter_provenance"]
    assert terminal_failure["model_call_accounting_complete"] is False
    assert target_adapter_model_call_accounting_valid(terminal_failure) is False
