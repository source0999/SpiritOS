# Campaign 0 Segment 0C LumaCart Repair Evidence - 2026-07-25

## Status

Evidence packet for `Campaign 0 Segment 0C`.

This packet records reproduction, root cause, repair scope, validation, and the registered-suite blocker for the isolated Source Proxy Campaign 0 base branch.

The LumaCart reproduction and root-cause facts below were collected before the production repair was committed. This document is committed before the repair commit. The file was authored after the first uncommitted repair patch was applied, so the sequencing limitation is recorded explicitly.

## Scope

- Product scope: Source Proxy.
- Worktree: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`.
- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`.
- Accepted base construction commit: `bf6c73114d22e4947dcee8629a29352e3aeded82`.
- Segment 0B addendum commit: `495d03ebb1fcee1e8b18e8bbabf452f401af880b`.
- Campaign 3.5 source commit considered for disposition: `6616846d7584af0318fe18fbaf7c3b1195ea03b0`.

## Reproduction

Command:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_decision_target_plugin_orchestrator.py::test_active_lumacart_prompt_packet_uses_authoritative_orchestrator \
  -vv \
  --tb=long
```

Observed pre-repair result:

- Test failed.
- HTTP status: `409`.
- Reason code: `coding_semantic_review_scope_invalid`.
- Truth status: `BLOCKED_SAFE`.
- Canonical owner: `CodingOrchestrator`.

The failure occurred after the mocked coder model returned the intended six-file LumaCart bundle and before approval, apply, deterministic review pass/fail disposition, or verifier execution.

## Affected Path Authority

The LumaCart prompt `coder-001-init-dummy-product-site` proposed exactly these six files:

- `tests/ui-agent-trials/fixtures/dummy-product-site/README.md`
- `tests/ui-agent-trials/fixtures/dummy-product-site/package.json`
- `tests/ui-agent-trials/fixtures/dummy-product-site/index.html`
- `tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js`
- `tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js`
- `tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css`

Before repair, semantic review authority collapsed to the architect plan primary target only:

- `tests/ui-agent-trials/fixtures/dummy-product-site/README.md`

The target-owned prompt contract already carried the correct six-file path authority, but the semantic-review binding did not consistently use it.

## Root Cause

Classification: target-artifact binding and multi-file create-bundle scope handling defect.

Primary causes:

- `source_proxy/target_plugins/adapter.py::resolve_target_plugin` exposed LumaCart `allowed_actions` as action verbs even though downstream target-plugin review identity uses this field as writable artifact authority.
- `source_proxy/planning/plan.py::review_task_spec_from_plan` rejected exact server-owned path authority when the architect plan's base target contained only the primary file.
- `source_proxy/coding/orchestrator.py::_build_semantic_review_binding` only used target-plugin authority for adapters requiring an architect plan, so exact path-like server authority from LumaCart was ignored.
- Multi-file create bundles lacked baseline review snapshots. For an exact create-only bundle where every changed file is introduced from `/dev/null`, synthetic empty baseline snapshots are the correct closed-form baseline.

Negative classification:

- Not an incorrect test expectation.
- Not a task-spec authority error in the test packet.
- Not over-broad deterministic review; deterministic review was not reached in the failing path.
- Not adapter materialization; the proposed diff changed the intended six files.
- Not an approval or apply mismatch.
- Not a copy or cherry-pick from `6616846d`.

## Repair Summary

Production files changed:

- `source_proxy/target_plugins/adapter.py`
- `source_proxy/planning/plan.py`
- `source_proxy/coding/orchestrator.py`

Test files changed:

- `source_proxy/tests/test_target_plugin_adapter.py`
- `source_proxy/tests/test_review_task_spec_authority.py`

Repair behavior:

- Bind LumaCart identity to exact prompt-contract writable files instead of action verbs.
- Permit exact server-owned path authority to form a `create_file_bundle` review task when all changed files are explicitly authorized.
- Use path-like target-plugin authority for semantic-review binding and binding validation.
- Synthesize empty review snapshots only for exact create-only bundles whose diff sections all start from `/dev/null`.

## Validation

Focused LumaCart and new authority tests:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_review_task_spec_authority.py::test_exact_server_authority_can_bind_create_bundle_before_review \
  source_proxy/tests/test_review_task_spec_authority.py::test_exact_server_authority_still_rejects_unlisted_artifact \
  source_proxy/tests/test_target_plugin_adapter.py::test_lumacart_identity_binds_exact_writable_contract_paths \
  source_proxy/tests/test_decision_target_plugin_orchestrator.py::test_active_lumacart_prompt_packet_uses_authoritative_orchestrator \
  -vv \
  --tb=short
```

Result: `4 passed in 3.35s`.

Focused affected suites:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_review_task_spec_authority.py \
  source_proxy/tests/test_target_plugin_adapter.py \
  source_proxy/tests/test_decision_target_plugin_orchestrator.py
```

Result: `367 passed in 4.52s`.

Segment 0B focused baseline rerun:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_canonical_context_broker.py \
  source_proxy/tests/test_context_source_readiness.py \
  source_proxy/tests/test_prompt_packet_context_metadata.py \
  --tb=short
```

Result: `99 passed, 2 skipped in 19.05s`.

Coding orchestrator suite:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_coding_orchestrator.py \
  --tb=short
```

Result: `41 passed in 11.63s`.

## Registered Regression Blocker

Exact registered command:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
npm run test:coding-regression
```

Result:

```text
> spirit-os@0.1.0 test:coding-regression
> .venv-campaign1/bin/python -m pytest -q source_proxy/tests/test_coding_regression_pack.py

sh: 1: .venv-campaign1/bin/python: not found
```

Fallback execution of the same registered test file with the accepted Source Proxy runner:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_coding_regression_pack.py \
  --tb=short
```

Result: `3 failed, 136 passed, 46 subtests passed in 34.71s`.

The same three failures reproduce at clean addendum commit `495d03ebb1fcee1e8b18e8bbabf452f401af880b` in a temporary named comparison worktree, so they are base-preexisting and not introduced by the Segment 0C repair:

- `test_bounded_proposal_diff_preview_ignores_json_envelope_requirements`
- `test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target`
- `test_prompt_packet_live_trial_reuses_hidden_allowed_existing_agent_lab_target`

Because of the missing registered venv and the base-preexisting coding pack failures, Segment 0C cannot be called registered-regression green from this evidence alone.

## Anti-Overfit Notes

The repair does not special-case benchmark identifiers, private scorer strings, Campaign 3.5 evidence, or the `6616846d` source changes. The only LumaCart-specific production binding is the existing target-plugin contract import used to expose exact prompt-contract path authority.
