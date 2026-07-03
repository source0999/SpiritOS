from __future__ import annotations

import json
from pathlib import Path

from source_proxy.tasks.long_running import propose_dummy_product_site_render_cards_diff


FIXTURE_ROOT = Path("tests/ui-agent-trials/fixtures/dummy-product-site")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_prompt3_fixture(root: Path) -> None:
    _write(
        root / FIXTURE_ROOT / "index.html",
        "\n".join(
            [
                "<!doctype html>",
                '<main id="product-list"></main>',
                '<script src="src/main.js"></script>',
            ]
        )
        + "\n",
    )
    _write(root / FIXTURE_ROOT / "src/main.js", "console.log('LumaCart');\n")
    _write(
        root / FIXTURE_ROOT / "src/products.js",
        "\n".join(
            [
                "const products = [",
                "  { id: 'a', name: 'Desk Lamp', category: 'Lighting', description: 'Desk light', price: '$20' },",
                "  { id: 'b', name: 'Coffee Maker', category: 'Kitchen', description: 'Hot coffee', price: '$35' },",
                "  { id: 'c', name: 'Water Bottle', category: 'Fitness', description: 'Cold water', price: '$15' },",
                "  { id: 'd', name: 'Wireless Mouse', category: 'Office', description: 'Fast pointer', price: '$25' },",
                "  { id: 'e', name: 'Canvas Tote', category: 'Travel', description: 'Carry goods', price: '$18' },",
                "  { id: 'f', name: 'Notebook Set', category: 'Stationery', description: 'Three notebooks', price: '$12' },",
                "];",
                "export default products;",
            ]
        )
        + "\n",
    )
    _write(root / FIXTURE_ROOT / "src/styles.css", ".product-card { display: block; }\n")


def _clean_prompt3_bundle() -> str:
    return json.dumps(
        {
            "action": "create_file_bundle",
            "files": [
                {
                    "path": str(FIXTURE_ROOT / "index.html").replace("\\", "/"),
                    "content_lines": [
                        "<!doctype html>",
                        '<main id="product-list"></main>',
                        '<script type="module" src="src/main.js"></script>',
                    ],
                },
                {
                    "path": str(FIXTURE_ROOT / "src/main.js").replace("\\", "/"),
                    "content_lines": [
                        "import products from './products.js';",
                        "const list = document.querySelector('#product-list');",
                        "list.innerHTML = '';",
                        "products.forEach((product) => {",
                        "  const card = document.createElement('article');",
                        "  card.className = 'product-card';",
                        "  card.innerHTML = `<h2>${product.name}</h2><p>${product.category}</p><p>${product.description}</p><strong>${product.price}</strong>`;",
                        "  list.appendChild(card);",
                        "});",
                    ],
                },
            ],
        }
    )


def _fallback_trigger_bundle() -> str:
    return json.dumps(
        {
            "action": "create_file_bundle",
            "files": [
                {
                    "path": str(FIXTURE_ROOT / "index.html").replace("\\", "/"),
                    "content_lines": [
                        "<!doctype html>",
                        '<main id="product-list"></main>',
                        '<script type="module" src="src/main.js"></script>',
                    ],
                },
                {
                    "path": str(FIXTURE_ROOT / "src/main.js").replace("\\", "/"),
                    "content_lines": [
                        "const list = document.querySelector('#product-list');",
                        "list.textContent = 'Model forgot products';",
                    ],
                },
            ],
        }
    )


def test_prompt3_model_authored_payload_runs_python_anticheat_and_passes(tmp_path: Path) -> None:
    _seed_prompt3_fixture(tmp_path)

    payload = propose_dummy_product_site_render_cards_diff(
        task="Render LumaCart product cards from src/products.js.",
        workspace_root=tmp_path,
        llm_call=lambda *_args: _clean_prompt3_bundle(),
        model_alias="coder",
    )

    diagnostics = payload["coder_diagnostics"]
    assert diagnostics["anti_cheat_status"] == "pass"
    assert diagnostics["anti_cheat_report"]["checked_detector_ids"]
    assert diagnostics["trial_result_trust_status"] == "model_authored_diff_proven"
    assert payload["reason_code"] == "dummy_product_site_prompt3_bundle"


def test_prompt3_deterministic_recovery_payload_runs_python_anticheat_and_blocks(tmp_path: Path) -> None:
    _seed_prompt3_fixture(tmp_path)

    payload = propose_dummy_product_site_render_cards_diff(
        task="Render LumaCart product cards from src/products.js.",
        workspace_root=tmp_path,
        llm_call=lambda *_args: _fallback_trigger_bundle(),
        model_alias="coder",
    )

    diagnostics = payload["coder_diagnostics"]
    assert diagnostics["fallback_used"] is True
    assert diagnostics["anti_cheat_status"] == "fail"
    assert "fallback_labeled_primary_success" in diagnostics["anti_cheat_hard_fail_ids"]
    assert diagnostics["trial_result_trust_status"] == "anti_cheat_registry_blocked"
    assert payload["reason_code"] == "anti_cheat_registry_fail"
    assert payload["coder_blocked"] is True
