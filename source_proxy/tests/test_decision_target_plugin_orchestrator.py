from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import router as decision_router
from source_proxy.api.long_running_tasks import router as long_running_tasks_router
from source_proxy.approval.campaign_authority import ROOT as APPROVAL_ROOT
from source_proxy.coding.orchestrator import reset_coding_orchestrator_service_for_tests
from source_proxy.routing.litellm_router import clear_router_cache
from source_proxy.tasks.long_running import (
    coding_orchestrator_state_for_task,
    reset_long_running_tasks,
)
from source_proxy.target_plugins.adapter import (
    EXECUTION_PROFILE,
    FIXTURE_ROOT,
    LUMACART_PLUGIN_ID,
    PROMPT_CONTEXTS,
    TARGET_PLUGIN_SCHEMA_VERSION,
)


PROMPT_ID = "coder-001-init-dummy-product-site"
TARGET = f"{FIXTURE_ROOT}README.md"


def _model_response() -> str:
    products = [
        {
            "id": f"product-{number}",
            "name": f"Product {number}",
            "price": number * 10,
            "category": "Home" if number % 2 else "Office",
            "description": f"Description for product {number}.",
        }
        for number in range(1, 7)
    ]
    files = {
        "README.md": "# LumaCart\n\nAn isolated model-authored storefront.\n",
        "package.json": json.dumps(
            {
                "name": "lumacart-dummy",
                "private": True,
                "type": "module",
                "scripts": {"smoke": "node src/main.js"},
            },
            separators=(",", ":"),
        )
        + "\n",
        "index.html": (
            '<main id="app"><h1>LumaCart</h1></main>\n'
            '<script type="module" src="./src/main.js"></script>\n'
        ),
        "src/products.js": (
            f"export const products = {json.dumps(products, separators=(',', ':'))};\n"
        ),
        "src/main.js": "\n".join(
            [
                "import { products } from './products.js';",
                "const app = document.querySelector('#app');",
                "products.forEach((product) => {",
                "  const card = document.createElement('article');",
                "  card.className = 'product-card';",
                "  card.innerHTML = `<h2>${product.name}</h2><p>${product.category}</p><p>${product.description}</p><strong>$${product.price}</strong>`;",
                "  app.appendChild(card);",
                "});",
                "",
            ]
        ),
        "src/styles.css": (
            "body { font-family: system-ui, sans-serif; }\n"
            ".product-card { border: 1px solid #ddd; padding: 1rem; }\n"
        ),
    }
    return json.dumps(
        {
            "action": "create_file_bundle",
            "files": [
                {
                    "path": f"{FIXTURE_ROOT}{path}",
                    "content_lines": content.rstrip("\n").split("\n"),
                }
                for path, content in files.items()
            ],
        }
    )


def _target_plugin_packet() -> dict[str, object]:
    return {
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": LUMACART_PLUGIN_ID,
            "fixture_root": FIXTURE_ROOT,
            "selected_prompt_id": PROMPT_ID,
            "selected_context_id": PROMPT_CONTEXTS[PROMPT_ID],
            "execution_profile": EXECUTION_PROFILE,
        }
    }


def _acknowledgement_for_consumer(
    receipt: dict[str, object], consumer: str
) -> dict[str, object]:
    acknowledgements = receipt["runtime_acknowledgements"]
    assert isinstance(acknowledgements, list)
    matches = [
        item
        for item in acknowledgements
        if isinstance(item, dict)
        and isinstance(item.get("payload"), dict)
        and item["payload"].get("consumer") == consumer
    ]
    assert len(matches) == 1, matches
    return matches[0]


def test_active_lumacart_prompt_packet_uses_authoritative_orchestrator(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # The production authority identity is established when the API modules are
    # imported.  Exercise that registered, non-detached worktree instead of
    # substituting a synthetic identity; this route only proposes a diff.
    workspace = Path(APPROVAL_ROOT)
    assert not (workspace / TARGET).exists()

    monkeypatch.setenv("SPIRIT_PROJECT_PATH", str(workspace))
    monkeypatch.setenv("SOURCE_PROXY_PROJECT_ROOTS", str(workspace))
    monkeypatch.setenv("SPIRITOS_APPROVAL_ROOT", str(workspace))
    monkeypatch.setenv("SPIRITOS_APPROVAL_STATE_DIR", str(tmp_path / "approval-state"))
    monkeypatch.setenv(
        "SOURCE_PROXY_LONG_RUNNING_TASKS_DB", str(tmp_path / "tasks.sqlite3")
    )
    monkeypatch.setenv(
        "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG", str(tmp_path / "actions.jsonl")
    )
    monkeypatch.setenv("SOURCE_PROXY_FIP0_RECEIPT_DIR", str(tmp_path / "fip0"))
    monkeypatch.setenv("SOURCE_PROXY_FIP1_CONTEXT_ENABLED", "0")
    monkeypatch.setenv("SOURCE_PROXY_FIP2_RESEARCH_ENABLED", "0")
    monkeypatch.setenv("SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED", "0")
    monkeypatch.setenv("SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA", "0")
    monkeypatch.setenv("SOURCE_PROXY_CODER_MODEL_ALIAS", "openai")
    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "openai")
    monkeypatch.delenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-model-response-only")

    reset_long_running_tasks()
    reset_coding_orchestrator_service_for_tests()
    clear_router_cache()
    app = FastAPI()
    app.include_router(long_running_tasks_router)
    app.include_router(decision_router)
    client = TestClient(app)
    task = (
        f"Target file: {TARGET}\n"
        "Create the isolated LumaCart fixture as a six-file coder-agent storefront."
    )

    try:
        created_response = client.post(
            "/v1/tasks/long-running",
            json={"description": task},
        )
        assert created_response.status_code == 200, created_response.text
        created = created_response.json()
        task_id = created["task"]["id"]
        assert created["coding_orchestrator"]["authoritative"] is True

        with (
            mock.patch(
                "source_proxy.api.decision.execute_target_plugin_command",
                side_effect=AssertionError(
                    "active target-plugin request bypassed CodingOrchestrator"
                ),
            ) as direct_adapter,
            mock.patch(
                "source_proxy.tasks.long_running._call_coder_llm",
                return_value=_model_response(),
            ) as model_response,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "active_task_id": task_id,
                    "current_agent_role": "coder",
                    "selected_target": TARGET,
                    "allowed_files": [f"{FIXTURE_ROOT}**"],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_result_state": "PASS_DUMMY_PROJECT_INIT",
                    "selected_prompt_id": PROMPT_ID,
                    "dummy_coder_10_packet": _target_plugin_packet(),
                },
            )

        assert response.status_code == 200, response.text
        direct_adapter.assert_not_called()
        model_response.assert_called_once()

        payload = response.json()
        assert payload["target_plugin_orchestrated"] is True
        assert payload["status"] == "preview_ready"
        receipt = payload["coding_orchestrator"]
        assert receipt["authoritative"] is True
        assert receipt["task_id"] == task_id
        assert receipt["lane_states"]["planner"] == "completed"

        proposal = payload["target_plugin_proposal"]
        assert proposal == receipt["target_plugin_proposal"]
        assert proposal["status"] == "ready_for_approval_preview"
        assert proposal["selected_prompt_id"] == PROMPT_ID
        assert payload["runtime_output_id"] == proposal["runtime_output_id"]
        assert payload["target_plugin_output_id"] == proposal["runtime_output_id"]
        assert receipt["target_plugin_output_id"] == proposal["runtime_output_id"]
        assert payload["context_hash"] == proposal["context_hash"]
        assert payload["target_plugin_context_hash"] == proposal["context_hash"]
        assert (
            proposal["canonical_context_report"]["canonical_report_hash"]
            == proposal["context_hash"]
        )

        outputs = {
            item["output_id"]: item for item in receipt["runtime_outputs"]
        }
        consumptions = {
            item["consumption_id"]: item
            for item in receipt["runtime_consumptions"]
        }

        planner_ack = _acknowledgement_for_consumer(receipt, "planner")
        planner_context_output = outputs[planner_ack["output_id"]]
        planner_consumption = next(
            item
            for item in receipt["runtime_consumptions"]
            if item["acknowledgement_id"] == planner_ack["acknowledgement_id"]
        )
        assert planner_context_output["lane_id"] == "context-broker"
        assert (
            planner_ack["payload"]["context_hash"]
            == planner_context_output["payload"]["context_hash"]
        )
        assert planner_ack["artifact_hash"] == planner_context_output["artifact_hash"]
        assert planner_consumption["artifact_hash"] == planner_context_output["artifact_hash"]
        assert (
            planner_consumption["consumer_invocation_id"]
            == planner_ack["consumer_invocation_id"]
        )
        planner_output = next(
            item
            for item in receipt["runtime_outputs"]
            if item["lane_id"] == "planner"
        )
        assert (
            planner_output["producer_invocation_id"]
            == planner_ack["consumer_invocation_id"]
        )

        coder_ack = _acknowledgement_for_consumer(receipt, "coder")
        coder_context_output = outputs[coder_ack["output_id"]]
        coder_consumption = consumptions[proposal["context_consumption_id"]]
        assert coder_ack["output_id"] == proposal["context_runtime_output_id"]
        assert (
            coder_ack["acknowledgement_id"]
            == proposal["context_consumer_acknowledgement_id"]
        )
        assert coder_ack["payload"]["context_hash"] == proposal["context_hash"]
        assert coder_context_output["payload"]["context_hash"] == proposal["context_hash"]
        assert coder_consumption["output_id"] == proposal["context_runtime_output_id"]
        assert (
            coder_consumption["consumer_invocation_id"]
            == proposal["producer_model_invocation_id"]
        )
        assert (
            outputs[proposal["runtime_output_id"]]["producer_invocation_id"]
            == proposal["producer_model_invocation_id"]
        )

        persisted = coding_orchestrator_state_for_task(task_id)
        assert persisted is not None
        assert persisted["run_id"] == receipt["run_id"]
        persisted_proposal = persisted["target_plugin_proposal"]
        assert (
            persisted_proposal["proposal_binding_sha256"]
            == proposal["proposal_binding_sha256"]
        )
        assert persisted_proposal["runtime_output_id"] == proposal["runtime_output_id"]
        persisted_identity = persisted_proposal["target_plugin_identity"]
        assert persisted_identity == proposal["target_plugin_identity"]
        assert isinstance(persisted_identity["allowed_actions"], list)
        assert persisted_identity == json.loads(
            json.dumps(persisted_identity, sort_keys=True)
        )
        # This focused route test starts from a task, not a Cartographer
        # selection. Cartographer acknowledgement is required only when a real
        # selection/transfer was supplied; that production boundary is covered
        # by test_cartographer_coding_orchestrator and the clean proving run.
        assert receipt["cartographer_finalization"] is None

        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value=_model_response(),
        ):
            taskless_response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": task,
                    "selected_target": TARGET,
                    "allowed_files": [f"{FIXTURE_ROOT}**"],
                    "wants_implementation": True,
                    "needs_codebase_context": True,
                    "trial_mode": "live_apply",
                    "expected_result_state": "PASS_DUMMY_PROJECT_INIT",
                    "selected_prompt_id": PROMPT_ID,
                    "dummy_coder_10_packet": _target_plugin_packet(),
                },
            )
        assert taskless_response.status_code == 200, taskless_response.text
        taskless = taskless_response.json()
        assert taskless["target_plugin_orchestrated"] is False
        taskless_diagnostics = taskless["coder_diagnostics"]
        assert taskless_diagnostics["terminal_proof_eligible"] is False
        assert taskless_diagnostics["target_plugin_orchestrated"] is False
        assert (
            taskless_diagnostics["claim_ceiling"]
            == "unorchestrated_preview_only"
        )
    finally:
        reset_long_running_tasks()
        reset_coding_orchestrator_service_for_tests()
        clear_router_cache()
