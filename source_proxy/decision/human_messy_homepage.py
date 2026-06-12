from __future__ import annotations

import difflib
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from source_proxy.decision.task_spec_intake import (
    build_task_spec_intake,
    intake_as_legacy_task_spec,
)
from source_proxy.decision.tool_action_executor import ToolActionWorkspaceContract
from source_proxy.decision.tool_action_loop import (
    BoundedAgentLoopRequest,
    run_bounded_agent_loop,
)


DEFAULT_HUMAN_MESSY_HOMEPAGE_PROMPT = "init a repo and make homepage for agent lab expermients"
DEFAULT_ALLOWED_FILES = ("index.html", "styles.css")
DEFAULT_MODEL_ID = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_API = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class HumanMessyHomepagePaths:
    workspace: Path
    receipt_path: Path
    score_path: Path
    transcript_path: Path
    diff_path: Path


def run_human_messy_homepage(
    *,
    prompt: str,
    workspace: Path,
    receipt_path: Path,
    score_path: Path,
    transcript_path: Path,
    diff_path: Path,
    preview_url: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    adapter_source: str = "ollama_generate/tool_action_runtime_v1",
    model_call: Callable[[dict[str, Any]], str] | None = None,
    ollama_api: str = DEFAULT_OLLAMA_API,
) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    before = _snapshot(workspace)
    task_spec_intake = build_task_spec_intake(
        prompt,
        workspace_root=workspace,
        wants_implementation=True,
        model_lane="coder_agent",
    )
    legacy_task_spec = intake_as_legacy_task_spec(task_spec_intake)
    contract = ToolActionWorkspaceContract(
        workspace_root=workspace,
        allowed_files=tuple(task_spec_intake.allowed_files or DEFAULT_ALLOWED_FILES),
        forbidden_files=tuple(task_spec_intake.forbidden_files),
        protected_paths=tuple(task_spec_intake.protected_paths),
        approval_level="disposable_workspace",
        network_allowed=False,
        run_timeout_seconds=10,
    )
    request = BoundedAgentLoopRequest(
        task_spec=legacy_task_spec,
        context_packet={
            "user_prompt": prompt,
            "transparent_default_target": "index.html",
            "workspace_mode": "disposable_workspace",
            "allowed_files": list(contract.allowed_files),
            "forbidden_real_repo_mutation": True,
        },
        workspace_contract=contract,
        model_id=model_id,
        adapter_source=adapter_source,
        source_message_id="human-messy-homepage",
        recommended_checks=(),
        run_recommended_checks=False,
        max_format_retries=2,
        max_verification_repairs=0,
    )

    def call_model(packet: dict[str, Any]) -> str:
        if model_call is not None:
            return model_call(packet)
        return _ollama_generate(
            _render_model_prompt(packet),
            model_id=model_id,
            ollama_api=ollama_api,
        )

    started = time.monotonic()
    result = run_bounded_agent_loop(request, call_model, receipt_path=receipt_path).to_dict()
    elapsed = round(time.monotonic() - started, 3)
    receipt = result["receipt"]
    raw_transcripts = list(receipt.get("raw_model_transcripts") or [])
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(
        "\n\n--- MODEL CALL ---\n\n".join(raw_transcripts),
        encoding="utf-8",
        errors="replace",
    )

    after = _snapshot(workspace)
    diff = _diff_snapshots(before, after)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(diff, encoding="utf-8", errors="replace")

    score = score_human_messy_homepage_result(
        prompt=prompt,
        workspace=workspace,
        receipt=receipt,
        model_id=model_id,
        adapter_source=adapter_source,
        preview_url=preview_url,
        elapsed_seconds=elapsed,
        raw_transcript_path=transcript_path,
        receipt_path=receipt_path,
    )
    score_path.parent.mkdir(parents=True, exist_ok=True)
    score_path.write_text(json.dumps(score, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return score


def score_human_messy_homepage_result(
    *,
    prompt: str,
    workspace: Path,
    receipt: dict[str, Any],
    model_id: str,
    adapter_source: str,
    preview_url: str,
    elapsed_seconds: float,
    raw_transcript_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    diagnostics = dict(receipt.get("diagnostics_packet") or {})
    raw_transcripts = list(receipt.get("raw_model_transcripts") or [])
    parsed_actions = list(receipt.get("parsed_actions") or [])
    files_touched = sorted(set(diagnostics.get("files_touched") or []))
    files_changed = _changed_files_from_receipt(receipt)
    index_path = workspace / "index.html"
    openable_homepage = _is_openable_homepage(index_path)
    file_equals_model_action_content = _file_equals_model_action_content(
        index_path,
        parsed_actions,
    )
    backend_created_content = index_path.exists() and not file_equals_model_action_content
    fallback_used = False
    deterministic_scaffold_used = False
    dummy_fixture_used = False
    real_app_touched = _real_app_touched(files_touched)
    actions_seen = len(parsed_actions)
    blocked_reasons = list(diagnostics.get("blocked_reasons") or [])
    reason_codes = _reason_codes(receipt)
    final_state = str(receipt.get("final_state") or "")
    status = "GO" if (
        final_state in {"completed", "partial"}
        and actions_seen >= 1
        and "index.html" in files_changed
        and openable_homepage
        and not real_app_touched
        and not fallback_used
        and not deterministic_scaffold_used
        and not dummy_fixture_used
        and not backend_created_content
        and file_equals_model_action_content
    ) else "NO-GO"
    if status != "GO":
        if actions_seen < 1:
            reason_codes.append("no_model_actions_or_path_bound_blocks")
        if "index.html" not in files_changed:
            reason_codes.append("index_html_not_changed")
        if not openable_homepage:
            reason_codes.append("openable_homepage_missing")
        if backend_created_content:
            reason_codes.append("backend_created_content_detected")

    return {
        "status": status,
        "final_state": final_state,
        "prompt": prompt,
        "model_id": model_id,
        "adapter_source": adapter_source,
        "raw_transcript_path": str(raw_transcript_path),
        "raw_model_transcript_count": len(raw_transcripts),
        "parsed_action_count": len(parsed_actions),
        "actions_seen": actions_seen,
        "files_changed": files_changed,
        "files_touched": files_touched,
        "openable_homepage": openable_homepage,
        "preview_url": preview_url,
        "real_app_touched": real_app_touched,
        "fallback_used": fallback_used,
        "deterministic_scaffold_used": deterministic_scaffold_used,
        "dummy_fixture_used": dummy_fixture_used,
        "backend_created_content": backend_created_content,
        "file_equals_model_action_content": file_equals_model_action_content,
        "blocked_reasons": blocked_reasons,
        "reason_codes": sorted(set(reason_codes)),
        "receipt_path": str(receipt_path),
        "workspace_path": str(workspace),
        "elapsed_seconds": elapsed_seconds,
    }


def _render_model_prompt(packet: dict[str, Any]) -> str:
    context = packet["context_packet"]
    observations = packet.get("observations") or []
    retry_note = ""
    if observations:
        retry_note = (
            "\nPrevious output could not be executed. Return only one supported action now. "
            f"Observations: {json.dumps(observations, ensure_ascii=False)}\n"
        )
    return (
        "You are Source Proxy's local coding model. The user gave a messy human prompt.\n"
        "Create the requested homepage only inside the disposable workspace.\n"
        "Do not touch the real app, do not run shell commands, do not use network, do not explain steps.\n"
        "Return exactly one model-authored file action, with no markdown fences and no extra prose.\n"
        "Use this JSON shape:\n"
        '{"action_type":"WriteFile","target":"index.html","arguments":{"content":"FULL HTML FILE BYTES HERE"},"reason":"Create the requested homepage."}\n'
        "The content string must contain the full HTML document for index.html.\n"
        "Allowed files are index.html and styles.css; prefer inline CSS in index.html unless you also author styles.css.\n"
        f"User prompt: {context['user_prompt']}\n"
        f"Transparent default target: {context['transparent_default_target']}\n"
        f"{retry_note}"
    )


def _ollama_generate(prompt: str, *, model_id: str, ollama_api: str) -> str:
    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 2200},
    }
    request = urllib.request.Request(
        f"{ollama_api.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        parsed = json.loads(response.read().decode("utf-8", errors="replace"))
    return str(parsed.get("response") or "")


def _snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def _diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in sorted(set(before) | set(after)):
        if before.get(name) == after.get(name):
            continue
        chunks.extend(
            difflib.unified_diff(
                before.get(name, "").splitlines(keepends=True),
                after.get(name, "").splitlines(keepends=True),
                fromfile=f"a/{name}",
                tofile=f"b/{name}",
            )
        )
    return "".join(chunks)


def _changed_files_from_receipt(receipt: dict[str, Any]) -> list[str]:
    changed: set[str] = set()
    for execution in receipt.get("executions") or []:
        result = execution.get("result") or {}
        if result.get("status") == "completed":
            changed.update(str(path) for path in result.get("files_touched") or [])
    return sorted(changed)


def _is_openable_homepage(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    return "<html" in text and "</html>" in text and "<body" in text


def _file_equals_model_action_content(path: Path, parsed_actions: list[dict[str, Any]]) -> bool:
    if not path.is_file():
        return False
    actual = path.read_text(encoding="utf-8", errors="replace")
    for action in parsed_actions:
        if action.get("action_type") != "WriteFile":
            continue
        if action.get("target") != "index.html":
            continue
        arguments = action.get("arguments") or {}
        if isinstance(arguments, dict) and arguments.get("content") == actual:
            return True
    return False


def _real_app_touched(files_touched: list[str]) -> bool:
    return any(
        path.startswith(("src/", "app/", "pages/", "source_proxy/", "scripts/"))
        for path in files_touched
    )


def _reason_codes(receipt: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for result in receipt.get("parse_results") or []:
        code = str(result.get("error_code") or "")
        if code:
            codes.append(code)
    for execution in receipt.get("executions") or []:
        code = str((execution.get("result") or {}).get("error_code") or "")
        if code:
            codes.append(code)
    return codes
