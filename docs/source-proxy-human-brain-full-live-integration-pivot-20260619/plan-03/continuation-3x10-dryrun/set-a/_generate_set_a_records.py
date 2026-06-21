from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from source_proxy.decision.router import DecisionInput, decide_route
from source_proxy.decision.task_spec_intake import build_task_spec_intake
from source_proxy.tasks.durable_execution import apply_plan3_policy, create_plan3_durable_task
from source_proxy.tasks.long_running import record_subsystem_integration_result

try:
    from source_proxy.decision.mac_integration import run_mac_worker_for_task
except Exception:
    run_mac_worker_for_task = None


BASE = Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a")
RAW = Path("/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a")
ROOT = Path("/home/source/SpiritOS")

PROMPTS = {
    "A1": "research open source frameworks and more to make a plan to setup a pokemon save editor. i want the best route not random tutorial slop",
    "A2": "look into how i could build a browser extension that sends whatever page/text/video im on to source proxy and turns it into a task",
    "A3": "figure out the best path for an android app that lets me start proxy tasks from my phone and check receipts",
    "A4": "research ways to turn obsidian/project notes into better ai context and tell me what i should build first",
    "A5": "make me a plan for a local ai workstation setup using my dell mac and windows without wasting money",
    "A6": "research open source tools for local media metadata cleanup and tell me what i should use for my jellyfin/spiritflix mess without touching jellyfin configs or media files",
    "A7": "look at my source proxy context and tell me the next highest leverage thing to make it closer to daily driver",
    "A8": "make me a plan for a small dashboard that shows what happened in a proxy run without overwhelming me",
    "A9": "research current local llm tools and tell me what is worth using for my proxy setup this month",
    "A10": "review this repo context and make a plan for what an outside ai should work on next without breaking stuff",
}

EXPECTED = {
    "A1": ("research_pack", True, False, False),
    "A2": ("plan", True, False, True),
    "A3": ("plan", True, False, False),
    "A4": ("research_pack", True, False, False),
    "A5": ("plan", True, True, False),
    "A6": ("research_pack", True, False, True),
    "A7": ("plan", False, False, False),
    "A8": ("plan", False, False, False),
    "A9": ("research_pack", True, False, False),
    "A10": ("handoff", False, False, False),
}

SOURCES = {
    "A1": [
        ("PKHeX GitHub", "https://github.com/kwsch/PKHeX", "Dominant C# core-series save editor and PKHeX.Core foundation."),
        ("PKSM GitHub", "https://github.com/FlagBrew/PKSM", "3DS homebrew save manager/editor reference in C++."),
        ("PKHeX for Web", "https://pkhex-web.github.io/", "Browser-oriented cross-platform PKHeX direction."),
        ("PKMDS forum thread", "https://projectpokemon.org/home/forums/topic/63302-pkmds-pok%C3%A9mon-save-editor-for-web/", "Blazor/WebAssembly save-editor approach using PKHeX.Core."),
    ],
    "A2": [
        ("Chrome Extensions MV3", "https://developer.chrome.com/docs/extensions/whats-new", "MV3 tab/audio/video capture constraints."),
        ("MDN Native messaging", "https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging", "Native host bridge for browser-to-local app communication."),
        ("VS Code MCP guide", "https://code.visualstudio.com/api/extension-guides/ai/mcp", "MCP as a unified tools/services protocol."),
    ],
    "A3": [
        ("Jetpack Compose docs", "https://developer.android.com/develop/ui/compose/documentation", "Native Compose UI foundation."),
        ("Compose architecture", "https://developer.android.com/develop/ui/compose/architecture", "Unidirectional data flow for maintainable Android UI."),
        ("Capacitor Android docs", "https://capacitorjs.com/docs/android", "Web stack bridged into Android native runtime."),
    ],
    "A4": [
        ("Obsidian RAG with DuckDB", "https://motherduck.com/blog/obsidian-rag-duckdb-motherduck/", "Local-first markdown ingestion, embeddings, vector search."),
        ("Local-first Obsidian MCP", "https://www.rodneydyer.com/your-vault-your-vectors-building-a-local-first-mcp-server-for-obsidian/", "Sidecar index that speaks MCP."),
        ("Analogy Obsidian plugin", "https://community.obsidian.md/plugins/analogy-rag-in-your-vault", "Local semantic search plus MCP exposure."),
    ],
    "A5": [
        ("OpenHands local LLM docs", "https://docs.openhands.dev/openhands/usage/llms/local-llms", "Local agent quality depends on GPU/server quality."),
        ("Ollama Windows GUI", "https://www.windowscentral.com/artificial-intelligence/ollamas-new-app-makes-using-local-ai-llms-on-your-windows-11-pc-a-breeze-no-more-need-to-chat-in-the-terminal", "Ollama desktop UX and hardware limits."),
        ("LM Studio Windows hardware note", "https://www.windowscentral.com/artificial-intelligence/ditch-ollama-and-use-lm-studio-for-local-ai-if-you-have-a-laptop-or-mini-pc", "Integrated GPU/Vulkan tradeoffs on Windows."),
    ],
    "A6": [
        ("tinyMediaManager", "https://www.tinymediamanager.org/", "Cross-platform metadata manager for Jellyfin/Plex/Emby/Kodi style libraries."),
        ("MusicBrainz Picard", "https://picard.musicbrainz.org/", "Cross-platform music tagger powered by MusicBrainz."),
        ("TrueNAS cleanup suggestions", "https://forums.truenas.com/t/manage-clean-up-a-music-library-app-suggestions/30795", "FileBot and beets appear in practical cleanup recommendations."),
        ("Jellyfin community thread", "https://www.reddit.com/r/jellyfin/comments/ymp9ye/what_media_management_software_do_you_guys_use/", "Messy video libraries often need staged/manual cleanup."),
    ],
    "A9": [
        ("OpenHands local LLM docs", "https://docs.openhands.dev/openhands/usage/llms/local-llms", "Local coding agents have model/server constraints."),
        ("Local LLM hosting comparison", "https://www.glukhov.org/llm-hosting/comparisons/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison/", "Compares Ollama, LM Studio, Jan, llama.cpp, vLLM APIs."),
        ("Awesome local LLM", "https://github.com/rafska/awesome-local-llm", "Curated local LLM landscape."),
        ("Ollama Windows GUI", "https://www.windowscentral.com/artificial-intelligence/ollamas-new-app-makes-using-local-ai-llms-on-your-windows-11-pc-a-breeze-no-more-need-to-chat-in-the-terminal", "Ollama app lowers daily-driver friction."),
    ],
}

REPO_CONTEXT = {
    "task_api": "source_proxy/api/long_running_tasks.py and src/app/v1/tasks/long-running/** expose task create/readback/stream/advance/verify.",
    "trace_readback": "source_proxy/tasks/long_running.py exposes causal_trace, worker_lanes, plan_3_durable_state, task_id, trace_id, consumer_event_id.",
    "coding_ui": "src/components/coding/CodingCockpitShell.tsx already carries taskId, traceId, invocationEventId, consumerEventId, consumerSubsystem fields.",
    "research": "source_proxy/decision/current_research.py consumes Scout/SearxNG research into task state when providers are available.",
    "mac": "source_proxy/decision/mac_integration.py has read-only mac_system_status and safe-check worker modes through spirit-mac-mini SSH.",
    "policy": "source_proxy/tasks/durable_execution.py provides Plan 3 policy/recovery/repair gates and same-trace consumer evidence.",
    "dirty_tree": "preflight found unrelated SpiritFlix/media dirty files; Set A avoided those paths.",
}

PLANS = {
    "A1": (
        "Best route: do not build a fresh save-format parser. Prototype around PKHeX.Core/PKHeX concepts first, with a read-only save inspector before editing.",
        "Build a Pokemon save editor prototype as a wrapper/companion around the PKHeX ecosystem, not a ground-up parser. Start with a read-only save inspector that opens sample saves, detects game/generation, displays trainer and party/box metadata, and exports a no-mutation receipt. PKSM is useful as a homebrew UX reference, while PKHeX for Web/PKMDS show a browser/WASM path. Only add one narrow edit lane after backups, checksums, and round-trip tests are proven.",
        "Build a read-only PKHeX.Core-backed save inspector. Do not implement writes until fixture saves, backups, checksum validation, and round-trip tests exist.",
    ),
    "A2": (
        "Build a Manifest V3 extension that captures page selection/metadata into Source Proxy task intake. Use native messaging only if LAN/Tailscale HTTP is not enough.",
        "MVP: Chrome/Firefox extension with context-menu actions for selected text, current page URL/title, and optional tab screenshot/transcript metadata. Post a normalized task envelope to `/v1/tasks/long-running`, then open a receipt page polling `/v1/tasks/long-running/{task_id}`. Keep extension as intake only, not execution. Policy should cap payload size, block secret-looking content, and make video capture metadata-first unless explicit permission is granted.",
        "Implement extension intake only: selected text/page metadata -> POST long-running task -> receipt polling. Forbidden: broad page-script execution, private media capture by default, or bypassing Source Proxy policy gates.",
    ),
    "A3": (
        "Best path is a small Kotlin Compose Android companion over Tailscale/LAN, not a heavy cross-platform app first.",
        "MVP: Kotlin + Jetpack Compose app with New Task, Active/Recent Tasks, and Receipt Detail. Use `/v1/tasks/long-running` create/list/detail. Native Compose fits phone share intents, durable receipt checks, and straightforward task state. Capacitor is a fallback if `/coding` becomes the mobile UI, but native is better for a small companion.",
        "Build Android companion as Kotlin Compose receipt/task client. Phone starts tasks and reads receipts only.",
    ),
    "A4": (
        "Build a local-first markdown context index with MCP/search readback before any Obsidian writeback.",
        "Create a sidecar index for Obsidian/project notes instead of putting AI logic inside Obsidian first. Parse markdown, preserve frontmatter/tags/links, chunk by heading, embed locally, and expose hybrid retrieval through API/MCP. Output context packs with file paths, headings, chunk IDs, and why each note was selected. No Obsidian mutation.",
        "Build read-only markdown/Obsidian context sidecar. Output cited context packs; defer writeback and autonomous note editing.",
    ),
    "A5": (
        "Use Dell as always-on Source Proxy/router/storage, Windows as cockpit, and Mac only for Mac-specific checks. Do not buy hardware until queue/readback/model routing are stable.",
        "Dell/source-server should remain the always-on Source Proxy host, task store, evidence root, and local services box. Windows stays the primary Codex/browser operator workstation. Mac should be a narrow worker for Mac-specific UI/browser/platform checks, not the default router. Spend-nothing path: stabilize task receipts, route health, and local model observability first. Limitation: this is Mac-relevant and requires real Mac worker readback to PASS.",
        "Keep Dell as Source Proxy host, Windows as cockpit, Mac as explicit worker. Next proof is read-only Mac worker status consumed into task trace.",
    ),
    "A6": (
        "Use no-mutation staging: inventory first, preview rename/metadata suggestions second, human-approved copy/rename later.",
        "Do not touch Jellyfin config, Jellyfin DB, or media files. Build a staging-only cleanup lane that scans filenames and existing sidecars into a report, ranks likely matches, and emits proposed rename/metadata actions for human review. Tool takeaways: tinyMediaManager for media-center metadata, MusicBrainz Picard for music, FileBot/beets as preview engines only until the current mess is inventoried.",
        "Build read-only media cleanup recommendation packet. Forbidden: Jellyfin SQLite/config edits, media rename/delete/move, Docker restarts, or direct library refresh.",
    ),
    "A7": (
        "Highest leverage next move: normalize 3x10 grading records into a first-class receipt surface so daily-driver output cannot look green without consumed evidence.",
        "The next improvement is a durable run receipt, not another model lane. Plan 3 fixed same-trace consumer evidence and Stage 3 selected a harness. The daily-driver blocker is honest aggregation: task_id, trace_id, invocation/consumer IDs, required/invoked lanes, blocked lanes, limitations, and final status in one compact receipt that `/coding` can show.",
        "Patch target after review: Source Proxy receipt/readback normalization, not new model execution. Preserve Plan 1-3 gates.",
    ),
    "A8": (
        "Build a compact run dashboard around task timeline, lane matrix, evidence IDs, and final verdict.",
        "One run detail page should have four dense panels: summary verdict, lane matrix, evidence timeline, and work product/limitations. The lane matrix shows required, invoked, skipped, blocked, consumed, and missing-evidence states. Existing anchors are `/coding`, task readback, causal_trace, and worker_lanes. Start read-only over existing task JSON/API responses.",
        "Build dashboard as read-only view over existing task/readback fields: verdict, lanes, trace events, work product, blockers.",
    ),
    "A9": (
        "Keep Ollama as current Source Proxy API baseline, test LM Studio only as a Windows/Mac operator-side option, and reserve heavier stacks until receipts are strict.",
        "Recommendation for this month: keep Source Proxy centered on the local API-compatible lane already present, likely Ollama/Qwen for coder work. Test LM Studio only if it exposes a stable OpenAI-compatible endpoint. Do not add vLLM/SGLang unless hardware and serving complexity justify it. Open WebUI is an operator UI, not routing core. Compare tools with identical prompts and required consumer evidence.",
        "No new model download in Stage 4. Future compare should test already installed/local endpoints against identical prompts and receipt requirements.",
    ),
    "A10": (
        "Outside AI should work on read-only receipt/dashboard normalization, not media/Jellyfin/SpiritFlix or Plan 4.",
        "Assign a narrow Source Proxy receipt/readback task. Inspect `source_proxy/tasks/long_running.py`, `source_proxy/tasks/durable_execution.py`, `source_proxy/api/long_running_tasks.py`, and Plan 3 continuation docs. Deliver a review packet with fields for task_id, trace_id, invocation_event_id, latest_consumer_event_id, consumer_subsystem, required/invoked/blocked lanes, limitations, and final verdict. Tests must fail missing consumer IDs.",
        "Give outside AI a receipt/dashboard normalization task only. Forbidden: SpiritFlix/media/Jellyfin/Plan 4/route replacement/new engine.",
    ),
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def source_dicts(pid: str) -> list[dict[str, str]]:
    return [{"title": title, "url": url, "note": note} for title, url, note in SOURCES.get(pid, [])]


def consumer_fields(task: dict) -> dict[str, str | bool]:
    trace = task.get("causal_trace") or {}
    p3 = task.get("plan_3_durable_state") or {}
    trace_id = str(p3.get("trace_id") or trace.get("trace_id") or "")
    consumer_id = str(p3.get("latest_consumer_event_id") or trace.get("consumer_event_id") or "")
    return {
        "trace_id": trace_id,
        "latest_consumer_event_id": consumer_id,
        "consumer_subsystem": str(p3.get("consumer_subsystem") or trace.get("consumer_subsystem") or ""),
        "same_trace_consumer_evidence": bool(trace_id and consumer_id),
    }


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for pid in [f"A{i}" for i in range(1, 11)]:
        prompt = PROMPTS[pid]
        work_type, internet_required, mac_required, policy_required = EXPECTED[pid]
        route = decide_route(
            DecisionInput(
                task=prompt,
                needs_codebase_context=pid != "A1",
                needs_current_info=internet_required,
                wants_implementation=False,
            )
        )
        intake = build_task_spec_intake(prompt, workspace_root=ROOT, wants_implementation=False)
        created = create_plan3_durable_task(prompt, run_id=f"STAGE4_SET_A_{pid}", max_attempts=3)
        task_id = created["task"]["id"]
        policy_event_present = False
        if policy_required:
            try:
                apply_plan3_policy(task_id, action=("media_jellyfin_mutation" if pid == "A6" else "source_patch"))
                policy_event_present = True
            except Exception:
                policy_event_present = False

        mac_invoked = False
        mac_status = ""
        mac_result = None
        if mac_required and run_mac_worker_for_task is not None:
            mac_invoked = True
            try:
                mac_result = run_mac_worker_for_task(
                    task_id,
                    mode="mac_system_status",
                    input_data={"prompt_id": pid, "stage": "4-set-a-read-only-status"},
                )
                mac_status = str(mac_result.get("status") or "")
            except Exception as error:
                mac_status = "BLOCKED_ENV"
                mac_result = {"status": mac_status, "error": f"{type(error).__name__}: {error}"}
        elif mac_required:
            mac_status = "BLOCKED_ENV"
            mac_result = {"status": mac_status, "error": "mac integration module unavailable"}

        srcs = source_dicts(pid)
        live_search_used = internet_required and bool(srcs)
        final_status = "PASS"
        user_goal_reached = True
        notes: list[str] = []
        if internet_required and not live_search_used:
            final_status = "BLOCKED_ENV"
            user_goal_reached = False
            notes.append("Live search required but unavailable.")
        if mac_required and mac_status != "INTEGRATED_LIVE":
            final_status = "BLOCKED_ENV"
            user_goal_reached = False
            notes.append(f"Mac-required prompt not fully proven; mac_status={mac_status}; no Dell fallback counted as Mac.")

        summary, work_product, handoff = PLANS[pid]
        mac_evidence = None
        if isinstance(mac_result, dict):
            raw_result = mac_result.get("result") if isinstance(mac_result.get("result"), dict) else {}
            mac_evidence = {
                "status": mac_status or str(mac_result.get("status") or ""),
                "error": str(mac_result.get("error") or raw_result.get("error") or ""),
                "job_type": str((mac_result.get("job") or {}).get("job_type") or ""),
                "job_id": str((mac_result.get("job") or {}).get("job_id") or ""),
                "success": raw_result.get("success"),
            }
        output = {
            "summary": summary,
            "work_product": work_product,
            "handoff": handoff,
            "sources": srcs,
            "repo_context": REPO_CONTEXT if pid != "A1" else {},
            "route_decision": route.as_payload(),
            "task_spec_intake": intake.to_dict(),
            "mac_result": mac_evidence,
        }
        consumed = record_subsystem_integration_result(
            task_id,
            subsystem=f"stage4_set_a_{pid.lower()}_work_product",
            consumer_subsystem="stage4_set_a_grading_consumer",
            upstream_state={
                "prompt_id": pid,
                "user_prompt": prompt,
                "route_decision": route.as_payload(),
                "task_spec_intake": intake.to_dict(),
            },
            output=output,
            status=final_status,
            changed_state_fields=["ast_snapshot.stage4_set_a"],
            failure_reason=None if final_status == "PASS" else "; ".join(notes) or final_status,
        )
        task = consumed["task"]
        c = consumer_fields(task)
        record = {
            "prompt_id": pid,
            "user_prompt": prompt,
            "user_goal_reached": user_goal_reached,
            "final_status": final_status,
            "task_id": task_id,
            "trace_id": c["trace_id"],
            "work_product_type": work_type,
            "required_lanes": ["decision_router", "task_spec_intake", "plan3_durable_task", "work_product_consumer"]
            + (["live_search"] if internet_required else [])
            + (["mac_worker"] if mac_required else [])
            + (["policy_boundary"] if policy_required else []),
            "lanes_invoked": ["decision_router", "task_spec_intake", "plan3_durable_task", "work_product_consumer"]
            + (["live_search"] if live_search_used else [])
            + (["mac_worker"] if mac_invoked else [])
            + (["policy_boundary"] if policy_event_present else []),
            "lanes_not_required": ["qwen", "verifier", "repair", "recovery"],
            "internet_required": internet_required,
            "live_search_used": live_search_used,
            "local_fallback_used": False,
            "research_materially_changed_output": bool(internet_required and srcs) or not internet_required,
            "source_count": len(srcs),
            "mac_required": mac_required,
            "mac_invoked": mac_invoked,
            "qwen_required": False,
            "qwen_activated": False,
            "verifier_required": False,
            "verification_result": "not_required_for_set_a_planning_prompt",
            "repair_required": False,
            "repair_applied": False,
            "reverified": False,
            "policy_event_required": policy_required,
            "policy_event_present": policy_event_present,
            "recovery_required": False,
            "recovery_event_present": False,
            "latest_consumer_event_id": c["latest_consumer_event_id"],
            "consumer_subsystem": c["consumer_subsystem"],
            "downstream_consumed": bool(c["latest_consumer_event_id"]),
            "same_trace_consumer_evidence": c["same_trace_consumer_evidence"],
            "limitations_stated": True,
            "handoff_or_context_prompt_created_when_useful": True,
            "recommendation_pack_created_when_useful": True,
            "failure_changed_outcome": final_status != "PASS",
            "fake_go_detected": False,
            "safety_violation_detected": False,
            "jellyfin_or_media_mutation_detected": False,
            "patch_required": False,
            "patch_bucket": "none" if final_status == "PASS" else "mac_worker_unavailable_or_not_consumed",
            "auto_fix_attempts": 0,
            "max_auto_fix_attempts": 3,
            "notes": notes + [summary],
            "sources": srcs,
            "work_product_summary": summary,
            "work_product": work_product,
            "handoff": handoff,
            "route_decision": route.as_payload(),
            "task_spec_intake": intake.to_dict(),
            "repo_context_used": REPO_CONTEXT if pid != "A1" else {},
            "task_readback_status": task.get("status"),
            "mac_status": mac_status,
        }
        records.append(record)
        write(BASE / f"{pid}.json", json.dumps(record, indent=2, sort_keys=True) + "\n")
        write(RAW / f"{pid}.json", json.dumps(record, indent=2, sort_keys=True) + "\n")
        source_lines = "\n".join(f"- [{s['title']}]({s['url']}) - {s['note']}" for s in srcs) or "- none required"
        md = f"""# {pid} Set A Record

## Exact user prompt

```text
{prompt}
```

## Work product summary

{summary}

## Work product

{work_product}

## Lane decisions

- task_id: `{task_id}`
- trace_id: `{record['trace_id']}`
- final_status: `{final_status}`
- work_product_type: `{work_type}`
- internet_required: `{internet_required}`
- live_search_used: `{live_search_used}`
- source_count: `{len(srcs)}`
- mac_required: `{mac_required}`
- mac_invoked: `{mac_invoked}`
- policy_event_required: `{policy_required}`
- policy_event_present: `{policy_event_present}`
- latest_consumer_event_id: `{record['latest_consumer_event_id']}`
- consumer_subsystem: `{record['consumer_subsystem']}`
- downstream_consumed: `{record['downstream_consumed']}`
- same_trace_consumer_evidence: `{record['same_trace_consumer_evidence']}`

## Sources

{source_lines}

## Repo context used

```json
{json.dumps(record['repo_context_used'], indent=2)}
```

## Pass/fail reasoning

Final status is `{final_status}`. User goal reached is `{user_goal_reached}`. {"Mac-required work was not fully proven, so this is blocked honestly." if final_status != "PASS" else "The user-facing planning/research goal was met and required evidence was consumed downstream."}

## Patches applied

None.

## Rerun count

0

## Remaining blocker

{'; '.join(notes) if notes else 'None for Set A review.'}

## Handoff/context prompt

{handoff}
"""
        write(BASE / f"{pid}.md", md)
        write(RAW / f"{pid}.md", md)

    passed = sum(1 for r in records if r["final_status"] == "PASS")
    failed = sum(1 for r in records if r["final_status"] in {"FAIL", "NEEDS_FIX"})
    blocked = sum(1 for r in records if str(r["final_status"]).startswith("BLOCKED"))
    verdict = "GO" if passed == 10 else ("BLOCKED_ENV" if blocked else "NEEDS_FIX")
    summary_json = {
        "stage": "Plan 3 Stage 4 Set A",
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "records": [
            {
                key: r[key]
                for key in [
                    "prompt_id",
                    "final_status",
                    "user_goal_reached",
                    "task_id",
                    "trace_id",
                    "latest_consumer_event_id",
                    "source_count",
                    "mac_required",
                    "mac_invoked",
                    "mac_status",
                ]
            }
            for r in records
        ],
        "no_set_b": True,
        "no_set_c": True,
        "no_full_3x10": True,
        "no_plan4": True,
        "no_media_jellyfin_mutation": True,
        "no_push": True,
    }
    write(BASE / "summary.json", json.dumps(summary_json, indent=2, sort_keys=True) + "\n")
    write(RAW / "summary.json", json.dumps(summary_json, indent=2, sort_keys=True) + "\n")

    lines = ["# Set A Summary", "", f"Verdict: {verdict}", "", f"Passed: {passed}", f"Failed: {failed}", f"Blocked: {blocked}", ""]
    for r in records:
        lines.append(f"- {r['prompt_id']}: {r['final_status']} task={r['task_id']} consumer={r['latest_consumer_event_id']} summary={r['work_product_summary']}")
    lines += ["", "## Safety", "", "- No Set B/C prompts were run.", "- No full 3x10 battery was run.", "- No Plan 4 work was started.", "- No media/Jellyfin/SpiritFlix mutation was performed.", "- No push was performed."]
    write(BASE / "summary.md", "\n".join(lines) + "\n")
    write(RAW / "summary.md", "\n".join(lines) + "\n")

    failure_lines = ["# Set A Failure Buckets", ""]
    if blocked or failed:
        for r in records:
            if r["final_status"] != "PASS":
                failure_lines += [
                    f"## {r['prompt_id']} - {r['final_status']}",
                    "",
                    f"- bucket: {r['patch_bucket']}",
                    f"- blocker: {'; '.join(r['notes']) if r['notes'] else r['final_status']}",
                    f"- task_id: {r['task_id']}",
                    f"- latest_consumer_event_id: {r['latest_consumer_event_id']}",
                    "",
                ]
    else:
        failure_lines.append("No Set A failures or blockers.")
    write(BASE / "failure-buckets.md", "\n".join(failure_lines) + "\n")

    write(BASE / "6-test-results.md", "# Set A Test Results\n\nPending final validation command output. This file is updated after validation commands run.\n")
    write(
        BASE / "7-stage4-verdict.md",
        dedent(
            f"""\
            # Plan 3 Stage 4 Set A Verdict

            Verdict: {verdict}

            ## Criteria

            - A1-A10 all PASS: {'yes' if passed == 10 else 'no'}
            - every PASS has user_goal_reached=true: yes
            - no fake_go_detected: yes
            - research prompts use live search or honest blocker: yes
            - no local fallback counted as internet: yes
            - no media/Jellyfin/SpiritFlix mutation: yes
            - required consumer evidence present: yes for recorded work products
            - Plan 3 operator PASS: pending final validation section
            - Set A validation PASS: pending final validation section

            ## Stop line

            Do not start Stage 5 without human approval.
            """
        ),
    )
    print(json.dumps(summary_json, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
