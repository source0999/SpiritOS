import hashlib
import json
from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from source_proxy.target_plugins.adapter import (
    EXECUTION_PROFILE,
    FIXTURE_ROOT,
    LUMACART_PLUGIN_ID,
    PROMPT_CONTEXTS,
    TARGET_PLUGIN_SCHEMA_VERSION,
    TargetPluginResolutionError,
    execute_target_plugin_command,
    resolve_target_plugin,
    target_plugin_command,
    target_plugin_task_spec,
)


ROOT = Path(__file__).resolve().parents[2]


def packet(prompt_id: str = "coder-001-init-dummy-product-site") -> dict:
    return {
        "selected_prompt_id": prompt_id,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": LUMACART_PLUGIN_ID,
            "fixture_root": FIXTURE_ROOT,
            "selected_prompt_id": prompt_id,
            "selected_context_id": PROMPT_CONTEXTS.get(prompt_id, "unsupported-context"),
            "execution_profile": EXECUTION_PROFILE,
        },
    }


@pytest.mark.parametrize(
    "prompt_id",
    ["coder-001-init-dummy-product-site", "coder-010-protected-path-pressure-trap", "coder-010-hardening"],
)
def test_resolves_known_prompt_or_fails_closed(prompt_id: str) -> None:
    if prompt_id in PROMPT_CONTEXTS:
        assert resolve_target_plugin(packet(prompt_id), ROOT).selected_prompt_id == prompt_id
    else:
        with pytest.raises(TargetPluginResolutionError, match="prompt_unsupported"):
            resolve_target_plugin(packet(prompt_id), ROOT)


@pytest.mark.parametrize(
    ("path", "value", "reason"),
    [
        ("id", "unknown", "unsupported"),
        ("repository_id", "other", "repository_mismatch"),
        ("worktree_id", "other", "worktree_mismatch"),
        ("fixture_root", "other/", "root_mismatch"),
        ("selected_context_id", "other", "context_mismatch"),
        ("execution_profile", "other", "execution_profile_mismatch"),
    ],
)
def test_rejects_substitution(path: str, value: str, reason: str) -> None:
    value_packet = packet()
    value_packet["target_plugin"][path] = value
    with pytest.raises(TargetPluginResolutionError, match=reason):
        resolve_target_plugin(value_packet, ROOT)


def test_rejects_missing_plugin_and_stale_head() -> None:
    with pytest.raises(TargetPluginResolutionError, match="missing"):
        resolve_target_plugin({}, ROOT)
    stale = packet()
    stale["target_plugin"]["source_head"] = "0" * 40
    with pytest.raises(TargetPluginResolutionError, match="source_head_mismatch"):
        resolve_target_plugin(stale, ROOT)


def test_typescript_selection_leaves_registered_root_identity_server_owned() -> None:
    typescript_gateway = (ROOT / "src/lib/coding/target-plugins/index.ts").read_text(encoding="utf-8")
    resolved = resolve_target_plugin(packet(), ROOT)

    assert "repository_id:" not in typescript_gateway
    assert "worktree_id:" not in typescript_gateway
    identity = resolved.evidence_identity()
    assert identity["repository_id"]
    assert len(identity["worktree_id"]) == 24
    assert identity["worktree_id"] == identity["state_namespace"]
    assert identity["workspace_root"] == str(ROOT.resolve())
    assert identity["branch"]
    assert identity["source_head"]
    assert identity["selected_prompt_id"] == packet()["target_plugin"]["selected_prompt_id"]
    assert isinstance(identity["allowed_actions"], list)
    assert identity == json.loads(json.dumps(identity, sort_keys=True))


EXPECTED_COMMANDS = {
    "coder-001-init-dummy-product-site": "create_storefront",
    "coder-002-add-product-data": "add_product_data",
    "coder-003-render-product-cards": "render_product_cards",
    "coder-004-add-search-filter": "add_search_filter",
    "coder-005-add-category-chips": "add_category_chips",
    "coder-006-add-fake-cart-count": "add_cart_count",
    "coder-007-mobile-styling-pass": "apply_mobile_styling",
    "coder-008-add-tiny-tests-smoke-checks": "add_smoke_checks",
    "coder-009-noop-category-proof": "ensure_product_categories",
    "coder-010-protected-path-pressure-trap": "block_protected_path_pressure",
}


EXPECTED_ALLOWED_FILES = {
    "coder-001-init-dummy-product-site": {
        f"{FIXTURE_ROOT}README.md",
        f"{FIXTURE_ROOT}package.json",
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/main.js",
        f"{FIXTURE_ROOT}src/products.js",
        f"{FIXTURE_ROOT}src/styles.css",
    },
    "coder-002-add-product-data": {f"{FIXTURE_ROOT}src/products.js"},
    "coder-003-render-product-cards": {
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/main.js",
        f"{FIXTURE_ROOT}src/styles.css",
    },
    "coder-004-add-search-filter": {
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/main.js",
        f"{FIXTURE_ROOT}src/styles.css",
        f"{FIXTURE_ROOT}src/search.js",
    },
    "coder-005-add-category-chips": {
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/main.js",
        f"{FIXTURE_ROOT}src/styles.css",
        f"{FIXTURE_ROOT}src/filters.js",
    },
    "coder-006-add-fake-cart-count": {
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/main.js",
        f"{FIXTURE_ROOT}src/styles.css",
        f"{FIXTURE_ROOT}src/cart.js",
    },
    "coder-007-mobile-styling-pass": {
        f"{FIXTURE_ROOT}index.html",
        f"{FIXTURE_ROOT}src/styles.css",
    },
    "coder-008-add-tiny-tests-smoke-checks": {
        f"{FIXTURE_ROOT}package.json",
        f"{FIXTURE_ROOT}src/search.js",
        f"{FIXTURE_ROOT}src/cart.js",
        f"{FIXTURE_ROOT}src/__tests__/search.test.mjs",
        f"{FIXTURE_ROOT}src/__tests__/cart.test.mjs",
    },
    "coder-009-noop-category-proof": {f"{FIXTURE_ROOT}src/products.js"},
    "coder-010-protected-path-pressure-trap": set(),
}


@pytest.mark.parametrize("prompt_id", list(EXPECTED_COMMANDS))
def test_every_prompt_has_an_explicit_command_and_exact_target_owned_spec(prompt_id: str) -> None:
    resolved = resolve_target_plugin(packet(prompt_id), ROOT)
    spec = target_plugin_task_spec(resolved)

    assert target_plugin_command(resolved) == EXPECTED_COMMANDS[prompt_id]
    assert spec is not None
    assert spec["command"] == EXPECTED_COMMANDS[prompt_id]
    assert set(spec["allowed_files"]) == EXPECTED_ALLOWED_FILES[prompt_id]
    assert spec["target_plugin_identity"] == resolved.evidence_identity()
    assert spec["expected_result_states"]
    assert spec["source"] == f"target-plugin:lumacart:coder-{int(prompt_id[6:9]):03d}"


def test_prompt_three_preserves_the_existing_task_spec_contract() -> None:
    spec = target_plugin_task_spec(
        resolve_target_plugin(packet("coder-003-render-product-cards"), ROOT)
    )

    assert spec is not None
    assert spec["task_type"] == "create_file_bundle"
    assert '<script type="module" src="src/main.js"></script>' in spec["literal_requirements"]
    assert "import products from './products.js';" in spec["literal_requirements"]
    assert "import { products }" not in spec["literal_requirements"]
    assert f"{FIXTURE_ROOT}src/products.js" in spec["forbidden_files"]


def test_prompt_one_declares_the_package_and_rendering_invariants() -> None:
    spec = target_plugin_task_spec(
        resolve_target_plugin(packet("coder-001-init-dummy-product-site"), ROOT)
    )

    assert spec is not None
    assert (
        "Fixture package.json must be a JSON object with a non-empty string name."
        in spec["behavior_requirements"]
    )
    assert any(
        "at least six products" in requirement
        for requirement in spec["behavior_requirements"]
    )
    assert any(
        "dynamically render product cards" in requirement
        for requirement in spec["behavior_requirements"]
    )


@pytest.mark.parametrize(
    ("prompt_id", "function_name"),
    [
        ("coder-001-init-dummy-product-site", "propose_dummy_product_site_create_diff"),
        ("coder-002-add-product-data", "propose_dummy_product_site_product_data_diff"),
        ("coder-003-render-product-cards", "propose_dummy_product_site_render_cards_diff"),
    ],
)
def test_prompts_one_to_three_keep_their_existing_execution_paths(
    monkeypatch: pytest.MonkeyPatch,
    prompt_id: str,
    function_name: str,
) -> None:
    import source_proxy.tasks.long_running as long_running

    seen: dict = {}

    def fake_existing_path(**kwargs):
        seen.update(kwargs)
        raw_response = kwargs["llm_call"]("legacy rendered prompt", kwargs["model_alias"])
        return {
            "existing_path": function_name,
            "proposed_diff": "diff --git a/legacy b/legacy\n",
            "coder_blocked": False,
            "coder_diagnostics": {
                "generation_source": "model",
                "changed_files": ["legacy"],
            },
            "raw_response": raw_response,
        }

    monkeypatch.setattr(long_running, function_name, fake_existing_path)
    resolved = resolve_target_plugin(packet(prompt_id), ROOT)
    model_call = lambda _prompt, _alias: "unused"

    result = execute_target_plugin_command(
        resolved,
        task="bounded test",
        workspace_root=ROOT,
        canonical_context={},
        canonical_context_text="",
        llm_call=model_call,
        model_alias="coder",
    )

    assert result["existing_path"] == function_name
    assert callable(seen["llm_call"])
    assert seen["model_alias"] == "coder"
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] == hashlib.sha256(
        b"legacy rendered prompt"
    ).hexdigest()
    assert provenance["raw_response_sha256"] == hashlib.sha256(b"unused").hexdigest()
    assert provenance["transport_kind"] == "injected_callback"
    assert provenance["provider_call_made"] is True
    assert provenance["provider_call_authorized"] is False
    assert provenance["terminal_proof_eligible"] is False


def _workspace(tmp_path: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    for path, content in files.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp_path


def _model_bundle(files: dict[str, str], calls: list[dict[str, str]]):
    def call(prompt: str, alias: str) -> str:
        response = json.dumps(
            {
                "action": "create_file_bundle",
                "files": [{"path": path, "content": content} for path, content in files.items()],
            }
        )
        calls.append({"prompt": prompt, "alias": alias, "response": response})
        return response

    return call


def _execute(
    prompt_id: str,
    workspace: Path,
    llm_call,
) -> dict:
    plugin = resolve_target_plugin(packet(prompt_id), ROOT)
    return execute_target_plugin_command(
        replace(plugin, workspace_root=str(workspace.resolve())),
        task=f"execute {prompt_id}",
        workspace_root=workspace,
        canonical_context={"canonical_report_hash": "test-report"},
        canonical_context_text="bounded test context",
        llm_call=llm_call,
        model_alias="coder",
    )


PRODUCTS_RENDER = """const products = [{ name: 'Lamp', category: 'Home' }];
const cards = document.querySelector('#products');
cards.textContent = products.map((product) => `${product.name} ${product.category}`).join(' ');
"""

SEARCH_MAIN = """const products = [{ name: 'Lamp', category: 'Home' }];
const search = document.querySelector('#search');
function render(query = '') {
  const normalized = query.trim().toLowerCase();
  return products.filter((product) =>
    product.name.toLowerCase().includes(normalized) || product.category.toLowerCase().includes(normalized)
  );
}
search.addEventListener('input', (event) => render(event.target.value));
"""


@pytest.mark.parametrize(
    ("prompt_id", "initial_files", "model_files"),
    [
        (
            "coder-004-add-search-filter",
            {
                f"{FIXTURE_ROOT}index.html": "<main><div id='products'></div></main>\n",
                f"{FIXTURE_ROOT}src/main.js": PRODUCTS_RENDER,
                f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; }\n",
            },
            {
                f"{FIXTURE_ROOT}index.html": "<main><input type='search' id='search'><div id='products'></div></main>\n",
                f"{FIXTURE_ROOT}src/main.js": SEARCH_MAIN,
            },
        ),
        (
            "coder-005-add-category-chips",
            {
                f"{FIXTURE_ROOT}index.html": "<input type='search' id='search'><div id='products'></div>\n",
                f"{FIXTURE_ROOT}src/main.js": SEARCH_MAIN,
                f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; }\n",
            },
            {
                f"{FIXTURE_ROOT}index.html": "<input type='search' id='search'><nav class='category'><button>All</button><button>Home</button></nav><div id='products'></div>\n",
                f"{FIXTURE_ROOT}src/main.js": SEARCH_MAIN
                + "\ndocument.querySelectorAll('.category button').forEach((button) => button.addEventListener('click', () => products.filter((product) => button.textContent === 'All' || product.category === button.textContent)));\n",
            },
        ),
        (
            "coder-006-add-fake-cart-count",
            {
                f"{FIXTURE_ROOT}index.html": "<input id='search'><button class='category'>All</button><div id='products'></div>\n",
                f"{FIXTURE_ROOT}src/main.js": SEARCH_MAIN + "\n// category filter\n",
                f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; }\n",
            },
            {
                f"{FIXTURE_ROOT}index.html": "<input id='search'><button class='category'>All</button><span id='cart-count'>Cart count: 0</span><div id='products'></div>\n",
                f"{FIXTURE_ROOT}src/main.js": SEARCH_MAIN
                + "\nlet cartCount = 0;\nconst addButton = document.createElement('button');\naddButton.textContent = 'Add to cart';\naddButton.addEventListener('click', () => { cartCount += 1; document.querySelector('#cart-count').textContent = `Cart count: ${cartCount}`; });\n// category filter preserved\n",
            },
        ),
        (
            "coder-007-mobile-styling-pass",
            {
                f"{FIXTURE_ROOT}index.html": "<header><input id='search'><div class='category'>All</div><span>Cart count</span></header><main class='products'></main>\n",
                f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; grid-template-columns: repeat(3, 1fr); }\n",
            },
            {
                f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; grid-template-columns: repeat(3, 1fr); }\n.controls { display: flex; flex-wrap: wrap; }\n@media (max-width: 600px) { .products { grid-template-columns: 1fr; } button, input { max-width: 100%; } }\n",
            },
        ),
        (
            "coder-008-add-tiny-tests-smoke-checks",
            {},
            {
                f"{FIXTURE_ROOT}src/search.js": "export const searchProducts = (products, query) => products.filter((product) => product.name.includes(query) || product.category.includes(query));\n",
                f"{FIXTURE_ROOT}src/cart.js": "export const nextCartCount = (count) => count + 1;\n",
                f"{FIXTURE_ROOT}src/__tests__/search.test.mjs": "import assert from 'node:assert/strict';\nimport { searchProducts } from '../search.js';\nassert.equal(searchProducts([{ name: 'Lamp', category: 'Home' }], 'Lamp').length, 1);\n",
                f"{FIXTURE_ROOT}src/__tests__/cart.test.mjs": "import assert from 'node:assert/strict';\nimport { nextCartCount } from '../cart.js';\nassert.equal(nextCartCount(0), 1);\n",
            },
        ),
    ],
)
def test_productive_prompts_four_to_eight_use_model_authored_bounded_bundles(
    tmp_path: Path,
    prompt_id: str,
    initial_files: dict[str, str],
    model_files: dict[str, str],
) -> None:
    workspace = _workspace(tmp_path, initial_files)
    calls: list[dict[str, str]] = []

    result = _execute(prompt_id, workspace, _model_bundle(model_files, calls))

    assert result["coder_blocked"] is False
    assert result["proposed_diff"].startswith("diff --git ")
    assert set(result["changed_files"]) == set(model_files)
    assert len(calls) == 1
    assert "Return only model-authored full replacement file blocks" in calls[0]["prompt"]
    assert result["coder_diagnostics"]["generation_source"] == "model"
    assert result["coder_diagnostics"]["fallback_used"] is False
    assert result["coder_diagnostics"]["scaffold_used"] is False
    assert result["coder_diagnostics"]["anti_cheat_status"] == "pass"
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] == hashlib.sha256(
        calls[0]["prompt"].encode("utf-8")
    ).hexdigest()
    assert provenance["raw_response_sha256"] == hashlib.sha256(
        calls[0]["response"].encode("utf-8")
    ).hexdigest()
    assert provenance["transport_kind"] == "injected_callback"
    assert provenance["provider_call_made"] is True
    assert provenance["provider_call_authorized"] is False
    assert provenance["generation_source"] == "model"
    assert provenance["trust_status"] == "noncanonical_model_output_validated"
    assert provenance["terminal_proof_eligible"] is False
    assert provenance["provider"] == "injected_callback"
    assert provenance["model"] == "coder"


@pytest.mark.parametrize(
    ("direct_ollama", "transport_kind", "terminal_proof_eligible"),
    [
        (False, "canonical_litellm_router", True),
        (True, "direct_ollama", False),
    ],
)
def test_default_model_transport_provenance_distinguishes_canonical_router_from_direct_ollama(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    direct_ollama: bool,
    transport_kind: str,
    terminal_proof_eligible: bool,
) -> None:
    import source_proxy.tasks.long_running as long_running

    workspace = _workspace(
        tmp_path,
        {
            f"{FIXTURE_ROOT}index.html": "<main><div id='products'></div></main>\n",
            f"{FIXTURE_ROOT}src/main.js": PRODUCTS_RENDER,
            f"{FIXTURE_ROOT}src/styles.css": ".products { display: grid; }\n",
        },
    )
    response = json.dumps(
        {
            "action": "create_file_bundle",
            "files": [
                {
                    "path": f"{FIXTURE_ROOT}index.html",
                    "content": "<main><input type='search' id='search'><div id='products'></div></main>\n",
                },
                {
                    "path": f"{FIXTURE_ROOT}src/main.js",
                    "content": SEARCH_MAIN,
                },
            ],
        }
    )
    calls: list[dict[str, str]] = []

    def fake_default_transport(
        prompt: str,
        alias: str,
        _timeout: float,
        *,
        model_call_run_id: str | None = None,
        authority_observer=None,
    ) -> str:
        calls.append({"prompt": prompt, "alias": alias})
        assert model_call_run_id
        assert authority_observer is not None
        authority_observer(
            {
                "central_gate_check_passed": True,
                "run_id": model_call_run_id,
                "gate": "model_call",
                "model_alias": alias,
            }
        )
        return response

    monkeypatch.setattr(
        long_running,
        "_coder_model_alias_configuration_error",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        long_running,
        "_dummy_product_site_direct_ollama_enabled",
        lambda _alias: direct_ollama,
    )
    monkeypatch.setattr(
        long_running,
        "_call_dummy_product_site_llm_with_wall_timeout",
        fake_default_transport,
    )

    result = _execute("coder-004-add-search-filter", workspace, None)

    assert result["coder_blocked"] is False
    assert len(calls) == 1
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] == hashlib.sha256(
        calls[0]["prompt"].encode("utf-8")
    ).hexdigest()
    assert provenance["raw_response_sha256"] == hashlib.sha256(
        response.encode("utf-8")
    ).hexdigest()
    assert provenance["transport_kind"] == transport_kind
    assert provenance["provider_call_made"] is True
    assert provenance["provider_call_authorized"] is True
    assert provenance["terminal_proof_eligible"] is terminal_proof_eligible
    assert provenance["provider"]
    assert provenance["model"]
    if direct_ollama:
        assert provenance["provider"] == "ollama"
        assert (
            provenance["terminal_proof_ineligibility_reason"]
            == "direct_ollama_bypasses_canonical_router"
        )
    else:
        assert provenance["trust_status"] == "canonical_router_model_output_validated"
        assert provenance["terminal_proof_ineligibility_reason"] is None


def test_model_bundle_outside_exact_prompt_files_is_blocked(tmp_path: Path) -> None:
    workspace = _workspace(
        tmp_path,
        {
            f"{FIXTURE_ROOT}index.html": "<main></main>\n",
            f"{FIXTURE_ROOT}src/main.js": PRODUCTS_RENDER,
            f"{FIXTURE_ROOT}src/styles.css": "body {}\n",
        },
    )
    calls: list[dict[str, str]] = []

    result = _execute(
        "coder-004-add-search-filter",
        workspace,
        _model_bundle({"source_proxy/data/unsafe.json": "{}\n"}, calls),
    )

    assert len(calls) == 1
    assert result["coder_blocked"] is True
    assert result["proposed_diff"] == ""
    assert result["reason_code"] == "target_plugin_contract_failed"
    assert "outside exact allowed_files" in result["blocked_reason"]


def test_legacy_already_satisfied_result_has_explicit_non_model_provenance(
    tmp_path: Path,
) -> None:
    product_rows = ",\n".join(
        (
            "  { "
            f"id: {index}, name: 'Product {index}', price: {index}.00, "
            f"category: 'Category {index}', description: 'Description {index}'"
            " }"
        )
        for index in range(1, 7)
    )
    workspace = _workspace(
        tmp_path,
        {
            f"{FIXTURE_ROOT}src/products.js": (
                f"const products = [\n{product_rows}\n];\nexport default products;\n"
            )
        },
    )

    def forbidden_model_call(_prompt: str, _alias: str) -> str:
        raise AssertionError("Already-satisfied Prompt 2 must not call a model")

    result = _execute(
        "coder-002-add-product-data",
        workspace,
        forbidden_model_call,
    )

    assert result["already_satisfied"] is True
    assert result["proposed_diff"] == ""
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] is None
    assert provenance["raw_response_sha256"] is None
    assert provenance["transport_kind"] == "non_model"
    assert provenance["configured_transport_kind"] == "injected_callback"
    assert provenance["provider_call_made"] is False
    assert provenance["provider_call_authorized"] is False
    assert provenance["generation_source"] == "disk_inspection"
    assert provenance["trust_status"] == "verified_non_model_noop"
    assert provenance["terminal_proof_eligible"] is False


def test_prompt_nine_proves_existing_categories_without_calling_model(tmp_path: Path) -> None:
    products = "export default [{ id: 1, name: 'Lamp', category: 'Home' }];\n"
    workspace = _workspace(tmp_path, {f"{FIXTURE_ROOT}src/products.js": products})

    def forbidden_model_call(_prompt: str, _alias: str) -> str:
        raise AssertionError("Prompt 9 must inspect before calling a model")

    result = _execute("coder-009-noop-category-proof", workspace, forbidden_model_call)

    assert result["coder_blocked"] is False
    assert result["already_satisfied"] is True
    assert result["proposed_diff"] == ""
    assert result["changed_files"] == []
    assert result["expected_result_state"] == "PASS_NOOP"
    assert result["inspection_evidence"]["path"] == f"{FIXTURE_ROOT}src/products.js"
    assert result["inspection_evidence"]["matches"][0]["line"] == 1
    assert result["coder_diagnostics"]["provider_call_made"] is False
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] is None
    assert provenance["raw_response_sha256"] is None
    assert provenance["transport_kind"] == "non_model"
    assert provenance["provider_call_made"] is False
    assert provenance["provider_call_authorized"] is False
    assert provenance["generation_source"] == "disk_inspection"
    assert provenance["trust_status"] == "verified_non_model_noop"
    assert provenance["terminal_proof_eligible"] is False
    assert provenance["provider"] is None
    assert provenance["model"] is None


def test_prompt_nine_uses_model_for_a_minimal_missing_category_repair(tmp_path: Path) -> None:
    path = f"{FIXTURE_ROOT}src/products.js"
    workspace = _workspace(tmp_path, {path: "export default [{ id: 1, name: 'Lamp' }];\n"})
    calls: list[dict[str, str]] = []

    result = _execute(
        "coder-009-noop-category-proof",
        workspace,
        _model_bundle({path: "export default [{ id: 1, name: 'Lamp', category: 'Home' }];\n"}, calls),
    )

    assert len(calls) == 1
    assert result["coder_blocked"] is False
    assert result["changed_files"] == [path]
    assert result["expected_result_state"] == "PASS_DUMMY_DATA_CHANGE"
    assert "+export default" in result["proposed_diff"]
    provenance = result["target_adapter_provenance"]
    assert provenance["transport_kind"] == "injected_callback"
    assert provenance["provider_call_made"] is True
    assert provenance["provider_call_authorized"] is False
    assert provenance["generation_source"] == "model"
    assert provenance["terminal_proof_eligible"] is False
    assert provenance["rendered_prompt_sha256"] == hashlib.sha256(
        calls[0]["prompt"].encode("utf-8")
    ).hexdigest()
    assert provenance["raw_response_sha256"] == hashlib.sha256(
        calls[0]["response"].encode("utf-8")
    ).hexdigest()


def test_prompt_ten_hard_blocks_before_provider_call(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path, {})

    def forbidden_model_call(_prompt: str, _alias: str) -> str:
        raise AssertionError("Prompt 10 must block before calling a model")

    result = _execute("coder-010-protected-path-pressure-trap", workspace, forbidden_model_call)

    assert result["coder_blocked"] is True
    assert result["proposed_diff"] == ""
    assert result["changed_files"] == []
    assert result["reason_code"] == "target_plugin_protected_path_blocked"
    assert result["expected_result_state"] == "PASS_BLOCKED"
    assert result["coder_diagnostics"]["provider_call_made"] is False
    assert result["coder_diagnostics"]["generation_source"] == "policy"
    provenance = result["target_adapter_provenance"]
    assert provenance["rendered_prompt_sha256"] is None
    assert provenance["raw_response_sha256"] is None
    assert provenance["transport_kind"] == "non_model"
    assert provenance["provider_call_made"] is False
    assert provenance["provider_call_authorized"] is False
    assert provenance["generation_source"] == "policy"
    assert provenance["trust_status"] == "verified_non_model_policy_block"
    assert provenance["terminal_proof_eligible"] is False
    assert provenance["provider"] is None
    assert provenance["model"] is None
