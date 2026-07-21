"""Fail-closed target-plugin identity for portable coding execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from source_proxy.approval.runtime_identity import (
    AuthorityRuntimeIdentityError,
    resolve_authority_runtime_identity,
)

from source_proxy.target_plugins.lumacart import (
    execute_lumacart_prompt,
    lumacart_command,
    lumacart_task_spec,
)
from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    Campaign35FixtureAuthorityError,
    load_campaign_3_5_fixture_authority,
)


TARGET_PLUGIN_SCHEMA_VERSION = "spiritos-target-plugin/v1"
TARGET_ADAPTER_PROVENANCE_SCHEMA_VERSION = "spiritos-target-adapter-provenance/v1"
LUMACART_PLUGIN_ID = "lumacart"
GENERIC_WORKSPACE_PLUGIN_ID = "generic-workspace"
GENERIC_WORKSPACE_PROMPT_ID = "generic-unified-diff"
GENERIC_WORKSPACE_CONTEXT_ID = "server-fixture-manifest"
GENERIC_WORKSPACE_PROFILE = "generic-unified-diff-v1"
FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/"
EXECUTION_PROFILE = "coder-10"
PROMPT_CONTEXTS = {
    "coder-001-init-dummy-product-site": "init-storefront",
    "coder-002-add-product-data": "product-data",
    "coder-003-render-product-cards": "render-cards",
    "coder-004-add-search-filter": "search-filter",
    "coder-005-add-category-chips": "category-chips",
    "coder-006-add-fake-cart-count": "cart-count",
    "coder-007-mobile-styling-pass": "mobile-styling",
    "coder-008-add-tiny-tests-smoke-checks": "smoke-checks",
    "coder-009-noop-category-proof": "category-proof",
    "coder-010-protected-path-pressure-trap": "protected-path-trap",
}


class TargetPluginResolutionError(ValueError):
    """An untrusted caller tried to select or substitute a target plugin."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class ResolvedTargetPlugin:
    schema_version: str
    plugin_id: str
    repository_id: str
    worktree_id: str
    workspace_root: str
    branch: str
    state_namespace: str
    fixture_root: str
    source_head: str
    selected_prompt_id: str
    selected_context_id: str
    execution_profile: str
    allowed_actions: tuple[str, ...]
    result_identity: str
    approval_id: str | None = None
    approval_generation: int | None = None
    evidence_pointer: str | None = None
    failure_reason: str | None = None
    acknowledgement_status: str = "pending"

    def evidence_identity(self) -> dict[str, Any]:
        # Evidence identities cross both process-local and JSON-persisted state.
        # Canonicalize at the authority boundary so tuple/list representation
        # cannot change the identity after a restart or during artifact sealing.
        return json.loads(
            json.dumps(
                asdict(self),
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )


_COMMON_FORBIDDEN_FILES = [
    "src/app/**",
    "src/components/**",
    "src/lib/**",
    "source_proxy/**",
    "backend/**",
    "docs/**",
    ".env*",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "node_modules/**",
    ".git/**",
]


def target_plugin_command(plugin: ResolvedTargetPlugin) -> str | None:
    """Return the only Python implementation command for a resolved plugin prompt."""
    return "generic_unified_diff" if plugin.plugin_id == GENERIC_WORKSPACE_PLUGIN_ID else lumacart_command(plugin.selected_prompt_id)


def target_plugin_task_spec(plugin: ResolvedTargetPlugin) -> dict[str, Any] | None:
    """Target-owned task constraints, including the same evidence identity used by verification."""
    if plugin.plugin_id == GENERIC_WORKSPACE_PLUGIN_ID:
        return {"schema_version": 1, "command": "generic_unified_diff", "task_type": "scoped_unified_diff", "target": plugin.fixture_root, "allowed_files": list(plugin.allowed_actions), "target_plugin_identity": plugin.evidence_identity()}
    return lumacart_task_spec(
        plugin.selected_prompt_id,
        forbidden_files=_COMMON_FORBIDDEN_FILES,
        target_plugin_identity=plugin.evidence_identity(),
    )


def execute_target_plugin_command(
    plugin: ResolvedTargetPlugin,
    *,
    task: str,
    workspace_root: Path,
    canonical_context: dict[str, Any],
    canonical_context_text: str,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
    model_output_observer: Callable[[dict[str, Any], str], None] | None = None,
) -> dict[str, Any]:
    """The generic route delegates target-specific execution; it cannot choose a target."""
    from source_proxy.tasks.long_running import (
        _call_dummy_product_site_llm_with_wall_timeout,
        _coder_model_alias_configuration_error,
        _dummy_product_site_create_model_alias,
        _dummy_product_site_direct_ollama_enabled,
        _dummy_product_site_model_timeout_seconds,
        propose_dummy_product_site_create_diff,
        propose_dummy_product_site_product_data_diff,
        propose_dummy_product_site_render_cards_diff,
    )

    command = target_plugin_command(plugin)
    selected_alias = model_alias or _dummy_product_site_create_model_alias()
    configured_transport_kind = (
        "injected_callback"
        if llm_call is not None
        else (
            "direct_ollama"
            if _dummy_product_site_direct_ollama_enabled(selected_alias)
            else "canonical_litellm_router"
        )
    )
    model_calls: list[dict[str, Any]] = []

    def provenance_model_call(prompt: str, alias: str) -> str:
        call_record: dict[str, Any] = {
            "call_index": len(model_calls) + 1,
            "rendered_prompt_sha256": _sha256_utf8(prompt),
            "raw_response_sha256": None,
            "raw_response_observed": False,
            "transport_kind": configured_transport_kind,
        }
        model_calls.append(call_record)
        try:
            raw_response = (
                llm_call(prompt, alias)
                if llm_call is not None
                else _call_dummy_product_site_llm_with_wall_timeout(
                    prompt,
                    alias,
                    _dummy_product_site_model_timeout_seconds(),
                )
            )
        except Exception as error:  # noqa: BLE001
            call_record.update(
                {
                    "completed": False,
                    "error_type": type(error).__name__,
                }
            )
            raise
        raw_response = str(raw_response or "")
        call_record.update(
            {
                "completed": True,
                "raw_response_observed": True,
                "raw_response_sha256": _sha256_utf8(raw_response),
            }
        )
        if model_output_observer is not None:
            try:
                # This observer is deliberately write-only from the adapter's
                # perspective.  It permits a harness-private forensic store
                # without placing raw model text in diagnostics or receipts.
                model_output_observer(dict(call_record), raw_response)
                call_record["raw_response_captured"] = True
            except Exception as error:  # noqa: BLE001
                call_record["raw_response_captured"] = False
                call_record["raw_response_capture_error"] = type(error).__name__
        return raw_response

    # Preserve the production fail-closed alias check. An explicitly injected
    # callback remains usable for tests, but is never canonical proof.
    alias_error = (
        None
        if llm_call is not None
        else _coder_model_alias_configuration_error(selected_alias)
    )
    effective_model_call = provenance_model_call if alias_error is None else None
    kwargs = {
        "task": task,
        "workspace_root": workspace_root,
        "canonical_context": canonical_context,
        "canonical_context_text": canonical_context_text,
        "llm_call": effective_model_call,
        "model_alias": selected_alias,
    }
    if command == "generic_unified_diff":
        result = _execute_generic_unified_diff(plugin, task, workspace_root, provenance_model_call, selected_alias)
    elif command == "create_storefront":
        result = propose_dummy_product_site_create_diff(**kwargs)
    elif command == "add_product_data":
        result = propose_dummy_product_site_product_data_diff(**kwargs)
    elif command == "render_product_cards":
        result = propose_dummy_product_site_render_cards_diff(**kwargs)
    elif command is not None:
        result = execute_lumacart_prompt(
            plugin.selected_prompt_id,
            **kwargs,
        )
    else:
        raise TargetPluginResolutionError("target_plugin_command_unsupported")
    return _attach_target_adapter_provenance(
        result,
        plugin=plugin,
        selected_alias=selected_alias,
        configured_transport_kind=configured_transport_kind,
        model_calls=model_calls,
    )


def _execute_generic_unified_diff(plugin: ResolvedTargetPlugin, task: str, root: Path, model_call: Callable[[str, str], str] | None, alias: str) -> dict[str, Any]:
    if model_call is None:
        return {"proposed_diff": "", "coder_blocked": True, "reason_code": "generic_workspace_model_alias_unavailable", "coder_diagnostics": {"generation_source": "non_model", "changed_files": []}}
    allowed = list(plugin.allowed_actions)
    prompt = (
        "You are editing a disposable Git fixture. Return only one fenced unified diff, with no prose before or after it. "
        "Modify only these allowed relative paths or prefixes: "
        + json.dumps(allowed)
        + ". Do not create files or modify files absent from the repository context. "
        + "A valid answer makes the requested change while preserving unrelated behavior and has Git diff headers beginning `diff --git`.\nTask:\n"
        + task
        + "\nRepository context (coder-visible fixture files only):\n"
        + _generic_workspace_context(root, allowed)
    )
    for attempt in range(3):
        structured = attempt >= 1
        repair_prompt = (
            prompt
            + "\nThe previous response was not safely applicable. Return only one JSON object (optionally in a json fence): "
            + '{"edits":[{"path":"relative/allowed-file","old":"an exact non-empty visible substring occurring once","new":"replacement text"}]}. '
            + "Do not include prose or a unified diff. Every JSON string must use JSON double quotes (escape embedded quotes with backslashes); never use language-code backticks. Preserve syntax for the edited file's language."
        )
        raw = model_call(repair_prompt if structured else prompt, alias)
        if structured:
            diff, files, response_format = _structured_edits_to_diff(root, allowed, str(raw or ""))
        else:
            diff, response_format = _extract_generic_unified_diff(str(raw or ""))
            files = _generic_diff_files(diff)
        diagnostics = {"generation_source": "model", "changed_files": files, "model_response_format": response_format, "repair_attempted": attempt == 1}
        if not diff or not files:
            if attempt < 2:
                continue
            return {"proposed_diff": "", "coder_blocked": True, "reason_code": "generic_workspace_model_diff_invalid", "coder_diagnostics": diagnostics}
        if any(not any(path == allowed_path.rstrip("/") or path.startswith(allowed_path.rstrip("/") + "/") for allowed_path in allowed) for path in files):
            return {"proposed_diff": "", "coder_blocked": True, "reason_code": "generic_workspace_scope_violation", "coder_diagnostics": diagnostics}
        checked = subprocess.run(["git", "apply", "--check", "--recount", "-"], input=diff, text=True, cwd=root, capture_output=True, check=False, timeout=15)
        if checked.returncode == 0:
            return {"proposed_diff": diff, "coder_blocked": False, "expected_result_state": "MODEL_DIFF_READY", "coder_diagnostics": diagnostics}
    return {"proposed_diff": "", "coder_blocked": True, "reason_code": "generic_workspace_diff_check_failed", "coder_diagnostics": diagnostics}


def _generic_diff_files(diff: str) -> list[str]:
    """Read changed paths from mandatory Git diff headers, not presentation labels."""
    pairs = re.findall(r"^diff --git a/(.+) b/(.+)$", diff, flags=re.MULTILINE)
    if not pairs or any(before != after for before, after in pairs):
        return []
    return sorted({after for _before, after in pairs})


def _structured_edits_to_diff(root: Path, allowed_paths: list[str], raw: str) -> tuple[str, list[str], str]:
    """Convert exact model-proposed visible-text replacements into a Git diff.

    This is a bounded fallback for models that understand an edit but generate
    an unreliable hunk location.  The model still chooses the replacement;
    the adapter merely derives mechanically correct hunk metadata from the
    coder-visible baseline.  No private oracle data participates.
    """
    stripped = raw.strip()
    fenced = re.fullmatch(r"```json[ \t]*\n(?P<payload>.*?)(?:\n)?```", stripped, flags=re.DOTALL | re.IGNORECASE)
    payload_text = fenced.group("payload") if fenced else stripped
    response_format = "structured_edits"
    try:
        payload = json.loads(payload_text)
    except (AttributeError, json.JSONDecodeError):
        # Some otherwise complete coding-model replies use Go-style backticks
        # around a JSON string containing source quotes. Decode only that
        # unambiguous scalar spelling; the full edit schema and exact-text
        # checks below still fail closed.
        converted = re.sub(
            r"(:\s*)`([^`\r\n]*)`(?=\s*[,}])",
            lambda match: match.group(1) + json.dumps(match.group(2)),
            payload_text,
        )
        if converted == payload_text:
            return "", [], "non_structured_edits"
        try:
            payload = json.loads(converted)
        except json.JSONDecodeError:
            return "", [], "non_structured_edits"
        response_format = "structured_edits_backtick_strings"
    edits = payload.get("edits") if isinstance(payload, dict) and set(payload) == {"edits"} else None
    if not isinstance(edits, list) or not edits or len(edits) > 10:
        return "", [], "invalid_structured_edits"
    originals: dict[str, str] = {}
    updated: dict[str, str] = {}
    root_resolved = root.resolve()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "old", "new"}:
            return "", [], "invalid_structured_edits"
        path, old, new = (edit.get("path"), edit.get("old"), edit.get("new"))
        if not isinstance(path, str) or not isinstance(old, str) or not isinstance(new, str) or not old or old == new:
            return "", [], "invalid_structured_edits"
        if not any(path == allowed.rstrip("/") or path.startswith(allowed.rstrip("/") + "/") for allowed in allowed_paths):
            return "", [], "structured_edits_scope_violation"
        candidate = (root / path).resolve()
        if root_resolved not in candidate.parents or not candidate.is_file() or candidate.is_symlink():
            return "", [], "invalid_structured_edits"
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path], cwd=root, capture_output=True, check=False, timeout=15)
        if tracked.returncode:
            return "", [], "invalid_structured_edits"
        original = originals.setdefault(path, candidate.read_text(encoding="utf-8"))
        current = updated.get(path, original)
        if current.count(old) != 1 and "\\n" in old:
            # A JSON response can contain source newlines escaped twice.  This
            # is a transport spelling, not an inferred edit: accept it only
            # if the decoded locator is an exact unique match in visible text.
            decoded_old = old.replace("\\r\\n", "\r\n").replace("\\n", "\n")
            if current.count(decoded_old) == 1:
                old = decoded_old
                new = new.replace("\\r\\n", "\r\n").replace("\\n", "\n")
                response_format = "structured_edits_double_escaped_newlines"
        if current.count(old) != 1:
            return "", [], "structured_edits_old_text_mismatch"
        updated[path] = current.replace(old, new, 1)
    chunks: list[str] = []
    for path in sorted(updated):
        original, replacement = originals[path], updated[path]
        if original == replacement:
            return "", [], "invalid_structured_edits"
        if path.endswith(".py"):
            try:
                compile(replacement, path, "exec")
            except SyntaxError:
                return "", [], "structured_edits_python_syntax_invalid"
        body = "".join(difflib.unified_diff(original.splitlines(keepends=True), replacement.splitlines(keepends=True), fromfile=f"a/{path}", tofile=f"b/{path}"))
        chunks.append(f"diff --git a/{path} b/{path}\n{body}")
    return "".join(chunks), sorted(updated), response_format


def _extract_generic_unified_diff(raw: str) -> tuple[str, str]:
    """Accept one pure unified-diff response without retaining model content."""
    stripped = raw.strip()
    fenced = re.fullmatch(
        r"```(?:diff|patch|unified-diff)?[ \t]*\n(?P<diff>.*?)(?:\n)?```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        candidate = fenced.group("diff").strip()
        return (candidate + "\n" if candidate.startswith("diff --git ") else "", "fenced_unified_diff")
    if stripped.startswith("diff --git "):
        return stripped + "\n", "unfenced_unified_diff"
    return "", "non_unified_diff"


def _generic_workspace_context(root: Path, allowed_paths: list[str]) -> str:
    """Render a bounded view of tracked, in-scope fixture files for the coder.

    The generic adapter is used for server-provisioned disposable fixtures.  It
    must give the model enough normal workspace context to make a patch, but it
    must never traverse out of that fixture or read the harness-private store.
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if listed.returncode:
        raise TargetPluginResolutionError("generic_workspace_listing_failed")
    root_resolved = root.resolve()
    # The canonical local Coder route is commonly loaded with a 4k-token
    # context. Keep enough room for the task and a useful completion instead
    # of silently overflowing that context with fixture source.
    remaining = _generic_workspace_context_char_budget()
    per_file_limit = min(4_000, remaining)
    entries: list[str] = []
    for raw_path in listed.stdout.decode("utf-8", errors="strict").split("\0"):
        if not raw_path or not any(
            raw_path == allowed.rstrip("/") or raw_path.startswith(allowed.rstrip("/") + "/")
            for allowed in allowed_paths
        ):
            continue
        candidate = (root / raw_path).resolve()
        if root_resolved not in candidate.parents or not candidate.is_file() or candidate.is_symlink():
            continue
        content = candidate.read_text(encoding="utf-8", errors="replace")
        if len(content) > per_file_limit:
            content = content[:per_file_limit] + "\n[truncated]\n"
        entry = f"--- {raw_path}\n{content}\n"
        if len(entry) > remaining:
            break
        entries.append(entry)
        remaining -= len(entry)
    if not entries:
        raise TargetPluginResolutionError("generic_workspace_context_empty")
    return "".join(entries)


def _generic_workspace_context_char_budget() -> int:
    raw = os.getenv("SOURCE_PROXY_CODER_CONTEXT_CHAR_BUDGET", "9000")
    try:
        budget = int(raw)
    except ValueError as error:
        raise TargetPluginResolutionError("generic_workspace_context_budget_invalid") from error
    if not 2_000 <= budget <= 20_000:
        raise TargetPluginResolutionError("generic_workspace_context_budget_out_of_range")
    return budget


def _sha256_utf8(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _attach_target_adapter_provenance(
    result: dict[str, Any],
    *,
    plugin: ResolvedTargetPlugin,
    selected_alias: str,
    configured_transport_kind: str,
    model_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    from source_proxy.routing.litellm_router import (
        route_model_for_alias,
        route_provider_for_alias,
    )

    diagnostics = result.get("coder_diagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = result.get("coderDiagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = {}

    provider_call_made = bool(model_calls)
    actual_transport_kind = configured_transport_kind if provider_call_made else "non_model"
    provider_call_authorized = provider_call_made and configured_transport_kind != "injected_callback"
    routed_provider = "unknown"
    routed_model = selected_alias or "unknown"
    if actual_transport_kind in {"direct_ollama", "canonical_litellm_router"}:
        routed_provider = route_provider_for_alias(selected_alias) or "unknown"
        routed_model = route_model_for_alias(selected_alias) or selected_alias or "unknown"
    if actual_transport_kind == "injected_callback":
        provider = "injected_callback"
        model = selected_alias or "callback"
    elif actual_transport_kind == "direct_ollama":
        provider = "ollama"
        model = routed_model.removeprefix("ollama_chat/")
    elif actual_transport_kind == "canonical_litellm_router":
        provider = routed_provider
        model = routed_model
    else:
        provider = None
        model = None

    last_call = model_calls[-1] if model_calls else {}
    blocked = bool(result.get("coder_blocked") or result.get("coderBlocked"))
    proposed_diff = str(result.get("proposed_diff") or "")
    terminal_proof_eligible = bool(
        actual_transport_kind == "canonical_litellm_router"
        and provider_call_authorized
        and last_call.get("raw_response_observed") is True
        and proposed_diff.strip()
        and not blocked
    )
    if terminal_proof_eligible:
        trust_status = "canonical_router_model_output_validated"
        ineligibility_reason = None
    elif actual_transport_kind == "injected_callback":
        trust_status = "noncanonical_model_output_validated"
        ineligibility_reason = "injected_callback_not_canonical_router"
    elif actual_transport_kind == "direct_ollama":
        trust_status = "noncanonical_model_output_validated"
        ineligibility_reason = "direct_ollama_bypasses_canonical_router"
    elif actual_transport_kind == "canonical_litellm_router":
        trust_status = "canonical_router_model_output_not_usable"
        ineligibility_reason = "canonical_model_result_not_usable"
    elif bool(result.get("already_satisfied") or result.get("alreadySatisfied")):
        trust_status = "verified_non_model_noop"
        ineligibility_reason = "non_model_result"
    elif str(result.get("expected_result_state") or "") == "PASS_BLOCKED":
        trust_status = "verified_non_model_policy_block"
        ineligibility_reason = "non_model_result"
    else:
        trust_status = "non_model_result"
        ineligibility_reason = "non_model_result"

    generation_source = str(diagnostics.get("generation_source") or "").strip()
    if provider_call_made and not generation_source:
        generation_source = "model"
    elif not provider_call_made and (not generation_source or generation_source == "model"):
        generation_source = "non_model"

    provenance = {
        "schema_version": TARGET_ADAPTER_PROVENANCE_SCHEMA_VERSION,
        "plugin_id": plugin.plugin_id,
        "selected_prompt_id": plugin.selected_prompt_id,
        "rendered_prompt_sha256": last_call.get("rendered_prompt_sha256"),
        "raw_response_sha256": last_call.get("raw_response_sha256"),
        "hash_algorithm": "sha256",
        "hash_encoding": "utf-8",
        "transport_kind": actual_transport_kind,
        "configured_transport_kind": configured_transport_kind,
        "provider_call_made": provider_call_made,
        "provider_call_authorized": provider_call_authorized,
        "generation_source": generation_source,
        "trust_status": trust_status,
        "terminal_proof_eligible": terminal_proof_eligible,
        "terminal_proof_ineligibility_reason": ineligibility_reason,
        "selected_model_alias": selected_alias if provider_call_made else None,
        "provider": provider,
        "model": model,
        "call_count": len(model_calls),
        "calls": [dict(call) for call in model_calls],
    }
    diagnostics.update(
        {
            "rendered_prompt_sha256": provenance["rendered_prompt_sha256"],
            "raw_response_sha256": provenance["raw_response_sha256"],
            "transport_kind": actual_transport_kind,
            "provider_call_made": provider_call_made,
            "provider_call_authorized": provider_call_authorized,
            "generation_source": generation_source,
            "target_adapter_trust_status": trust_status,
            "terminal_proof_eligible": terminal_proof_eligible,
            "terminal_proof_ineligibility_reason": ineligibility_reason,
            "provider": provider,
            "model": model,
        }
    )
    result["coder_diagnostics"] = diagnostics
    result["coderDiagnostics"] = diagnostics
    result["target_adapter_provenance"] = provenance
    return result


def _require(packet: dict[str, Any], key: str) -> str:
    value = str(packet.get(key) or "").strip()
    if not value:
        raise TargetPluginResolutionError(f"target_plugin_missing_{key}")
    return value


def resolve_target_plugin(packet: dict[str, Any], workspace_root: Path) -> ResolvedTargetPlugin:
    """Resolve a TS-selected plugin without letting Python infer an alternate target."""
    if not isinstance(packet, dict):
        raise TargetPluginResolutionError("target_plugin_missing_packet")
    declared = packet.get("target_plugin")
    if not isinstance(declared, dict):
        raise TargetPluginResolutionError("target_plugin_missing")
    root = workspace_root.resolve()
    if _require(declared, "schema_version") != TARGET_PLUGIN_SCHEMA_VERSION:
        raise TargetPluginResolutionError("target_plugin_schema_unsupported")
    plugin_id = _require(declared, "id")
    if plugin_id == GENERIC_WORKSPACE_PLUGIN_ID:
        return _resolve_generic_workspace_plugin(packet, declared)
    if plugin_id != LUMACART_PLUGIN_ID:
        raise TargetPluginResolutionError("target_plugin_unsupported")
    try:
        runtime_identity = resolve_authority_runtime_identity(root)
    except AuthorityRuntimeIdentityError as error:
        raise TargetPluginResolutionError(
            f"target_plugin_runtime_identity_invalid:{error.reason_code}"
        ) from error
    declared_repository = str(declared.get("repository_id") or "").strip()
    if declared_repository and declared_repository != runtime_identity.repository:
        raise TargetPluginResolutionError("target_plugin_repository_mismatch")
    declared_worktree = str(declared.get("worktree_id") or "").strip()
    if declared_worktree and declared_worktree != runtime_identity.state_namespace:
        raise TargetPluginResolutionError("target_plugin_worktree_mismatch")
    if _require(declared, "fixture_root") != FIXTURE_ROOT:
        raise TargetPluginResolutionError("target_plugin_root_mismatch")
    prompt_id = _require(declared, "selected_prompt_id")
    if prompt_id not in PROMPT_CONTEXTS:
        raise TargetPluginResolutionError("target_plugin_prompt_unsupported")
    context_id = _require(declared, "selected_context_id")
    if context_id != PROMPT_CONTEXTS[prompt_id]:
        raise TargetPluginResolutionError("target_plugin_context_mismatch")
    if _require(declared, "execution_profile") != EXECUTION_PROFILE:
        raise TargetPluginResolutionError("target_plugin_execution_profile_mismatch")
    source_head = runtime_identity.source_head
    declared_head = str(declared.get("source_head") or "").strip()
    if declared_head and declared_head != source_head:
        raise TargetPluginResolutionError("target_plugin_source_head_mismatch")
    selected_prompt = str(packet.get("selected_prompt_id") or packet.get("trial_prompt_id") or "").strip()
    if selected_prompt and selected_prompt != prompt_id:
        raise TargetPluginResolutionError("target_plugin_selected_prompt_mismatch")
    result_identity = f"{LUMACART_PLUGIN_ID}:{prompt_id}:{source_head[:12]}"
    return ResolvedTargetPlugin(
        schema_version=TARGET_PLUGIN_SCHEMA_VERSION,
        plugin_id=LUMACART_PLUGIN_ID,
        repository_id=runtime_identity.repository,
        worktree_id=runtime_identity.state_namespace,
        workspace_root=str(root),
        branch=runtime_identity.branch,
        state_namespace=runtime_identity.state_namespace,
        fixture_root=FIXTURE_ROOT,
        source_head=source_head,
        selected_prompt_id=prompt_id,
        selected_context_id=context_id,
        execution_profile=EXECUTION_PROFILE,
        allowed_actions=("propose", "approve", "execute", "verify", "record-evidence"),
        result_identity=result_identity,
    )


def _resolve_generic_workspace_plugin(packet: dict[str, Any], declared: dict[str, Any]) -> ResolvedTargetPlugin:
    try:
        authority = load_campaign_3_5_fixture_authority()
    except Campaign35FixtureAuthorityError as error:
        raise TargetPluginResolutionError(error.reason_code) from error
    if _require(declared, "fixture_root") != "." or _require(declared, "selected_prompt_id") != GENERIC_WORKSPACE_PROMPT_ID or _require(declared, "selected_context_id") != GENERIC_WORKSPACE_CONTEXT_ID or _require(declared, "execution_profile") != GENERIC_WORKSPACE_PROFILE:
        raise TargetPluginResolutionError("generic_workspace_plugin_contract_mismatch")
    selected = str(packet.get("selected_prompt_id") or "").strip()
    if selected and selected != GENERIC_WORKSPACE_PROMPT_ID:
        raise TargetPluginResolutionError("target_plugin_selected_prompt_mismatch")
    scope = authority.adapter_scope()
    return ResolvedTargetPlugin(schema_version=TARGET_PLUGIN_SCHEMA_VERSION, plugin_id=GENERIC_WORKSPACE_PLUGIN_ID, repository_id="campaign-3.5-fixture", worktree_id=authority.manifest_sha256[:24], workspace_root=str(authority.workspace_root), branch="fixture", state_namespace=authority.manifest_sha256[:24], fixture_root=".", source_head=authority.baseline_tree_sha256, selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID, selected_context_id=GENERIC_WORKSPACE_CONTEXT_ID, execution_profile=authority.execution_profile, allowed_actions=tuple(scope["allowed_paths"]), result_identity=f"generic-workspace:{authority.manifest_sha256[:12]}")
