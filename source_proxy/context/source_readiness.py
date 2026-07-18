from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from source_proxy.cartographer.blueprint_registry import list_blueprints
from source_proxy.cartographer.component_mapper import build_component_map
from source_proxy.cartographer.git_status import read_git_status_for_project
from source_proxy.cartographer.repo_map import build_repo_map_for_project
from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.context.obsidian import (
    ObsidianContextConfig,
    obsidian_context_config_from_env,
    query_obsidian_context,
)
from source_proxy.decision.scout_research import run_canonical_coding_research

ContextReadinessStatus = Literal[
    "used",
    "available",
    "skipped",
    "blocked",
    "unavailable",
    "failed",
]


@dataclass(frozen=True)
class ContextSourcePacket:
    source: str
    status: ContextReadinessStatus
    reason: str
    packet: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    authority: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


READ_ONLY_AUTHORITY = {
    "read_only": True,
    "can_apply": False,
    "can_commit": False,
    "can_push": False,
    "can_write_memory": False,
    "can_start_worker": False,
    "can_call_provider": False,
}


def build_cartographer_context_packet(
    task: str,
    *,
    project_root: Path | None = None,
    target_files: list[str] | None = None,
) -> ContextSourcePacket:
    root = (project_root or _project_root()).resolve()
    try:
        repo_map = build_repo_map_for_project(root.name.lower(), root)
        git_status = read_git_status_for_project(project_id=root.name.lower(), root=root)
        changed_files = list(getattr(git_status, "changed_files", []) or [])
        sample_paths = changed_files or target_files or _task_paths(task)
        component_map = build_component_map(sample_paths or None)
        blueprints = _blueprint_truth(root)
    except Exception as exc:
        return ContextSourcePacket(
            source="cartographer",
            status="blocked",
            reason=f"cartographer_packet_error: {exc}",
            diagnostics={"exception": type(exc).__name__},
            authority=dict(READ_ONLY_AUTHORITY),
        )

    indexed = int(getattr(repo_map, "files_indexed", 0) or 0)
    status: ContextReadinessStatus = "used" if indexed > 0 else "blocked"
    reason = "cartographer_packet_ready" if status == "used" else "repo_map_empty"
    dirty = bool(getattr(git_status, "dirty", False))
    return ContextSourcePacket(
        source="cartographer",
        status=status,
        reason=reason,
        packet={
            "repo_map": _compact_repo_map(repo_map),
            "component_map": _jsonable_component_map(component_map),
            "dirty_tree_status": {
                "available": bool(getattr(git_status, "available", False)),
                "dirty": dirty,
                "branch": getattr(git_status, "branch", None),
                "head_sha": getattr(git_status, "head_sha", None),
                "changed_files": changed_files[:50],
                "changed_file_count": len(changed_files),
            },
            "ownership_conflict_status": (
                "dirty_tree_present_review_required" if dirty else "no_dirty_tree_conflict_detected"
            ),
            "architecture_blueprint_truth": blueprints,
            "context_packet_adapter": {
                "schema_version": 1,
                "source": "cartographer",
                "emits": [
                    "repo_map",
                    "component_map",
                    "dirty_tree_status",
                    "ownership_conflict_status",
                    "architecture_blueprint_truth",
                ],
            },
        },
        diagnostics={
            "project_root": str(root),
            "files_indexed": indexed,
            "symbols_indexed": int(getattr(repo_map, "symbols_indexed", 0) or 0),
            "read_only": True,
        },
        authority=dict(READ_ONLY_AUTHORITY),
    )


def build_obsidian_context_packet(
    task: str,
    *,
    config: ObsidianContextConfig | None = None,
) -> ContextSourcePacket:
    cfg = config or obsidian_context_config_from_env()
    result = query_obsidian_context(task, config=cfg)
    raw_status = str(result.get("status") or "")
    notes = [note for note in result.get("notes", []) if isinstance(note, dict)]
    if raw_status == "used":
        status: ContextReadinessStatus = "used"
    elif raw_status in {"disabled", "no_relevant_notes"}:
        status = "skipped"
    else:
        status = "blocked"
    return ContextSourcePacket(
        source="obsidian",
        status=status,
        reason=raw_status or "obsidian_status_unknown",
        packet={
            "notes": [
                {
                    "title": str(note.get("title") or ""),
                    "path": str(note.get("path") or ""),
                    "safe_excerpt": _safe_context_excerpt(str(note.get("safe_excerpt") or "")),
                    "why_matched": str(note.get("why_matched") or ""),
                    "char_estimate": int(note.get("char_estimate") or 0),
                    "note_identity": str(note.get("note_identity") or ""),
                    "freshness": dict(note.get("freshness") or {}),
                    "stale": note.get("stale") is True,
                    "repository_conflict": note.get("repository_conflict") is True,
                }
                for note in notes
            ],
            "read_only": True,
            "used_skipped_blocked": status,
        },
        diagnostics=dict(result.get("diagnostics") or {}),
        authority=dict(READ_ONLY_AUTHORITY),
    )


async def build_scout_search_context_packet(
    task: str,
    *,
    max_results: int = 6,
) -> ContextSourcePacket:
    try:
        research = await run_canonical_coding_research(
            task_id=f"context-{abs(hash(task))}", query=task, max_results=max_results
        )
        sources = research.get("sources") if isinstance(research.get("sources"), list) else []
    except Exception as exc:
        return ContextSourcePacket(
            source="extended.scout-research",
            status="blocked",
            reason=f"research_packet_error: {exc}",
            diagnostics={"exception": type(exc).__name__},
            authority=dict(READ_ONLY_AUTHORITY),
        )
    public_sources = [_public_research_source(source) for source in sources]
    research_status = str(research.get("status") or "skipped")
    status: ContextReadinessStatus = (
        "used" if public_sources else research_status if research_status in {"skipped", "blocked", "failed", "unavailable"} else "skipped"
    )
    return ContextSourcePacket(
        source="extended.scout-research",
        status=status,
        reason=str(research.get("reason") or ("research_sources_selected" if public_sources else "no_research_sources_available")),
        packet={
            "sources": public_sources,
            "source_count": len(public_sources),
            "metadata_required": ["source", "freshness", "trust_status", "review_status"],
            "advisory_boundary": "evidence_only_no_code_or_memory_writes",
            "research_receipt": research,
        },
        diagnostics={
            "read_only": True,
            "hidden_memory_writes": False,
            "hidden_code_writes": False,
            "provider_call_made_by_adapter": True,
            "research_claim_ceiling": str(research.get("claim_ceiling") or "no_external_research_claim"),
        },
        authority=dict(READ_ONLY_AUTHORITY),
    )


def build_design_context_packet(
    task: str,
    *,
    project_root: Path | None = None,
) -> ContextSourcePacket:
    root = (project_root or _project_root()).resolve()
    design_refs = _design_refs(root, task)
    if not design_refs["component_refs"] and not design_refs["design_system_refs"]:
        status: ContextReadinessStatus = "blocked"
        reason = "design_context_unavailable"
    else:
        status = "used"
        reason = "design_context_ready"
    return ContextSourcePacket(
        source="design",
        status=status,
        reason=reason,
        packet={
            "design_system_refs": design_refs["design_system_refs"],
            "token_refs": design_refs["token_refs"],
            "component_refs": design_refs["component_refs"],
            "component_style_vocabulary": design_refs["component_style_vocabulary"],
            "ui_critique_packet": {
                "task_excerpt": _safe_context_excerpt(task)[:300],
                "critique_mode": "advisory_only",
                "visual_evidence_status": "path_refs_only",
            },
            "design_to_coder_handoff": {
                "authority": "advisory_context_only",
                "allowed": ["style vocabulary", "component references", "token references"],
                "forbidden": ["apply", "approval_token", "provider_call", "queue_worker", "git_mutation"],
            },
            "blocked_states": [] if status == "used" else ["missing_design_refs"],
        },
        diagnostics={
            "project_root": str(root),
            "read_only": True,
            "refs_found": sum(len(value) for value in design_refs.values() if isinstance(value, list)),
        },
        authority=dict(READ_ONLY_AUTHORITY),
    )


async def build_context_source_readiness_packet(
    task: str,
    *,
    project_root: Path | None = None,
    obsidian_config: ObsidianContextConfig | None = None,
    required_sources: Iterable[str] | None = None,
    source_states: Mapping[str, Mapping[str, Any]] | None = None,
    downstream_consumers: Mapping[str, Any] | None = None,
    applicable_consumers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build readiness metadata through the canonical context contract.

    Adapters report availability and packet contents.  Lifecycle callers must
    explicitly select/include sources and provide v2 consumer acknowledgements;
    adapter execution alone never proves downstream consumption.
    """

    packets = [
        build_cartographer_context_packet(task, project_root=project_root),
        build_obsidian_context_packet(task, config=obsidian_config),
        await build_scout_search_context_packet(task),
        build_design_context_packet(task, project_root=project_root),
    ]
    required = {
        str(source).strip()
        for source in (required_sources or ())
        if str(source).strip()
    }
    explicit_states = dict(source_states or {})
    broker_sources: list[dict[str, Any]] = []
    packet_source_names: set[str] = set()
    for packet in packets:
        packet_source_names.add(packet.source)
        source = packet.to_dict()
        state = explicit_states.get(packet.source)
        if isinstance(state, Mapping):
            source.update(dict(state))
        source["source"] = packet.source
        source["considered"] = source.get("considered") is not False
        source["required"] = source.get("required") is True or packet.source in required
        source["selected"] = source.get("selected") is True
        source["included"] = (
            source.get("included") is True
            or source.get("included_in_packet") is True
        )
        source["consumed"] = source.get("consumed") is True
        broker_sources.append(source)

    additional_source_names = list(
        dict.fromkeys(
            [
                *(
                    str(source).strip()
                    for source in explicit_states
                    if str(source).strip()
                ),
                *sorted(required),
            ]
        )
    )
    for source_name in additional_source_names:
        if source_name in packet_source_names:
            continue
        state = explicit_states.get(source_name)
        source = dict(state) if isinstance(state, Mapping) else {}
        source["source"] = source_name
        source["considered"] = source.get("considered") is not False
        source["status"] = str(source.get("status") or "unavailable")
        source["reason"] = str(
            source.get("reason") or "context_source_adapter_not_reported"
        )
        source["required"] = source.get("required") is True or source_name in required
        source["selected"] = source.get("selected") is True
        source["included"] = (
            source.get("included") is True
            or source.get("included_in_packet") is True
        )
        source["consumed"] = source.get("consumed") is True
        broker_sources.append(source)

    broker = build_context_broker_report(
        broker_sources,
        downstream_consumers=downstream_consumers,
        applicable_consumers=applicable_consumers,
    )
    return {
        "schema_version": 2,
        "task_excerpt": _safe_context_excerpt(task)[:300],
        "sources": broker["sources_considered"],
        "source_status": broker["source_status"],
        "canonical_context_broker": broker,
        "ready_for_source_proxy_packet": broker["go_eligible"],
        "authority": dict(READ_ONLY_AUTHORITY),
    }


def _project_root() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (candidate / "package.json").is_file() and (candidate / "source_proxy").is_dir():
            return candidate
    return Path.cwd()


def _task_paths(task: str) -> list[str]:
    return re.findall(
        r"(?:docs|_blueprints|src|source_proxy|scripts|tests)/[A-Za-z0-9._/@()[\]-]+",
        task or "",
    )[:20]


def _compact_repo_map(repo_map: Any) -> dict[str, Any]:
    data = asdict(repo_map)
    data["files"] = data.get("files", [])[:40]
    data["unmapped_paths"] = data.get("unmapped_paths", [])[:40]
    return data


def _jsonable_component_map(component_map: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in component_map.items():
        if isinstance(value, list):
            out[key] = [asdict(item) if hasattr(item, "__dataclass_fields__") else item for item in value]
        else:
            out[key] = value
    return out


def _blueprint_truth(root: Path) -> dict[str, Any]:
    try:
        records = [
            asdict(record)
            for record in list_blueprints()
            if not getattr(record, "project_id", "") or root.name.lower() in getattr(record, "project_id", "")
        ]
    except Exception:
        records = []
    if not records:
        blueprint_root = root / "_blueprints"
        if blueprint_root.is_dir():
            records = [
                {
                    "path": path.relative_to(blueprint_root).as_posix(),
                    "source_of_truth": path.name == "INDEX.md",
                }
                for path in sorted(blueprint_root.rglob("*.md"))[:20]
            ]
    return {
        "blueprint_count": len(records),
        "blueprints": records[:20],
        "status": "used" if records else "skipped_no_blueprints_found",
    }


def _public_research_source(source: dict[str, Any]) -> dict[str, Any]:
    evidence = source.get("evidence") if isinstance(source.get("evidence"), dict) else {}
    return {
        "title": _safe_context_excerpt(str(source.get("title") or ""))[:160],
        "url": str(source.get("url") or "")[:500],
        "snippet": _safe_context_excerpt(str(source.get("snippet") or ""))[:500],
        "source": str(source.get("source") or "unknown"),
        "evidence": {
            "source": str(evidence.get("source") or source.get("url") or ""),
            "freshness": str(evidence.get("freshness") or "unknown"),
            "trust_status": str(evidence.get("trust_status") or "unknown"),
            "review_status": str(evidence.get("review_status") or "unknown"),
            "packet_summary": _safe_context_excerpt(str(evidence.get("packet_summary") or ""))[:240],
            "why_relevant": _safe_context_excerpt(str(evidence.get("why_relevant") or ""))[:300],
        },
        "authority": str(source.get("authority") or "evidence_only"),
        "can_apply": False,
        "can_approve": False,
        "can_mutate_proxy_memory": False,
    }


def _design_refs(root: Path, task: str) -> dict[str, list[str]]:
    terms = {term for term in re.findall(r"[a-z0-9_-]{4,}", task.lower())}
    design_docs = sorted(root.glob("docs/design-agent*.md"))[:12]
    scout_design_docs = sorted(root.glob("docs/scout*v0-9*design*.md"))[:8]
    component_candidates = [
        root / "src/components/ui",
        root / "src/components/design-demo",
        root / "src/app/design-demo",
        root / "src/styles",
    ]
    component_refs: list[str] = []
    token_refs: list[str] = []
    vocabulary = [
        "layout_density",
        "component_reuse",
        "interaction_state",
        "visual_hierarchy",
        "responsive_fit",
        "token_alignment",
    ]
    for candidate in component_candidates:
        if not candidate.exists():
            continue
        for path in sorted(candidate.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".tsx", ".ts", ".css", ".md"}:
                rel = path.relative_to(root).as_posix()
                component_refs.append(rel)
                if "token" in rel.lower() or path.suffix.lower() == ".css":
                    token_refs.append(rel)
                if len(component_refs) >= 16:
                    break
    matched_docs = [
        path.relative_to(root).as_posix()
        for path in [*design_docs, *scout_design_docs]
        if not terms or any(term in path.name.lower() for term in terms) or "design" in path.name.lower()
    ][:16]
    return {
        "design_system_refs": matched_docs,
        "token_refs": token_refs[:12],
        "component_refs": component_refs[:16],
        "component_style_vocabulary": vocabulary,
    }


def _safe_context_excerpt(value: str) -> str:
    cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", value or "")
    cleaned = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-token]", cleaned)
    cleaned = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", cleaned)
    return " ".join(cleaned.split())
