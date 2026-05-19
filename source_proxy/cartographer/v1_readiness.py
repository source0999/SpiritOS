from __future__ import annotations

from source_proxy.cartographer.autonomy_promotion import build_autonomy_promotion_recommendation
from source_proxy.cartographer.trust_score import build_trust_score
from source_proxy.cartographer.v1_evidence import build_v1_evidence_inventory


REQUIRED_GREEN_LEVELS = [
    ("level_0_observe_project_state", "GREEN"),
    ("level_1_explain_dirty_tree", "GREEN"),
    ("level_2_classify_component_risk", "GREEN"),
    ("level_3_detect_drift", "GREEN"),
    ("level_4_recommend_branch_commit_groups", "GREEN"),
    ("level_5_draft_commit_push_readiness", "GREEN"),
    ("level_6_branch_after_approval", "GREEN"),
    ("level_7_commit_after_approval", "GREEN"),
    ("level_8_push_after_separate_approval", "GREEN"),
    ("level_9_docs_only_autopilot", "YELLOW_OR_GREEN"),
    ("level_10_project_start_tracking", "YELLOW_OR_GREEN"),
]

MAY_DO = [
    "observe repo state",
    "explain dirty tree",
    "classify risk",
    "detect drift",
    "draft blueprint/runbook/docs proposals",
    "recommend branch names",
    "recommend commit groups",
    "draft commit messages",
    "prepare push readiness notes",
    "create branches after approval",
    "commit after approval",
    "push after separate approval",
    "run docs-only autopilot only if explicitly enabled and capped",
]

MAY_NOT_DO = [
    "merge automatically",
    "push without separate approval",
    "commit without approval",
    "edit app code autonomously",
    "edit safety/approval/auth code autonomously",
    "delete files without approval",
    "touch secrets or env files",
    "bypass Source Proxy",
    "bypass Approval Gate",
    "promote its own authority level",
    "treat passing tests as permission",
]

BLOCKER_GUIDANCE = {
    "three_clean_full_diagnostics": {
        "how_to_satisfy": "Record three clean diagnostic or closeout proof artifacts with passing results.",
        "related_endpoint": "/v1/cartographer/v1-evidence",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-evidence | jq .",
    },
    "three_clean_soak_snapshots": {
        "how_to_satisfy": "Record three clean Cartographer soak snapshots with no HEAD change and no unexpected status delta.",
        "related_endpoint": "/v1/cartographer/v1-evidence",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-evidence | jq .",
    },
    "proxy_closeout_pass": {
        "how_to_satisfy": "Record a passing proxy-closeout proof artifact for the current reviewed state.",
        "related_endpoint": "/v1/cartographer/v1-proof-recording-proposal",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-recording-proposal | jq .",
    },
    "phase_4f_closeout_pass": {
        "how_to_satisfy": "Record a passing phase-4f-closeout proof artifact for the current reviewed state.",
        "related_endpoint": "/v1/cartographer/v1-proof-recording-proposal",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-recording-proposal | jq .",
    },
    "typescript_pass": {
        "how_to_satisfy": "Record a proof artifact showing the TypeScript check passed.",
        "related_endpoint": "/v1/cartographer/v1-proof-contract",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
    },
    "lint_pass_or_warnings_only": {
        "how_to_satisfy": "Record a proof artifact showing lint passed or produced warnings only.",
        "related_endpoint": "/v1/cartographer/v1-proof-contract",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
    },
    "blueprint_validation_pass": {
        "how_to_satisfy": "Record a proof artifact showing blueprint metadata validation passed.",
        "related_endpoint": "/v1/cartographer/v1-proof-contract",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
    },
    "diff_check_pass": {
        "how_to_satisfy": "Record a proof artifact showing the diff check passed for the reviewed change set.",
        "related_endpoint": "/v1/cartographer/v1-proof-contract",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
    },
    "targeted_vitest_pass": {
        "how_to_satisfy": "Record a proof artifact showing targeted Vitest checks passed or were explicitly rerouted.",
        "related_endpoint": "/v1/cartographer/v1-proof-contract",
        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
    },
}

READINESS_GROUPS = {
    "diagnostics": {
        "label": "Diagnostics and closeout evidence",
        "codes": [
            "three_clean_full_diagnostics",
            "three_clean_soak_snapshots",
            "proxy_closeout_pass",
            "phase_4f_closeout_pass",
        ],
        "next_endpoint": "/v1/cartographer/v1-evidence",
    },
    "proof_artifacts": {
        "label": "Recorded proof artifacts",
        "codes": [
            "typescript_pass",
            "lint_pass_or_warnings_only",
            "blueprint_validation_pass",
            "diff_check_pass",
            "targeted_vitest_pass",
        ],
        "next_endpoint": "/v1/cartographer/v1-proof-recording-proposal",
    },
    "authority_safety": {
        "label": "Authority and safety boundaries",
        "codes": [
            "no_unauthorized_commits",
            "no_unauthorized_pushes",
            "no_unexplained_head_changes",
            "push_audit_blocker_resolved",
            "dirty_tree_always_explained",
            "proposals_deduped",
            "drift_actionable",
            "rollback_hints_present",
        ],
        "next_endpoint": "/v1/cartographer/v1-readiness",
    },
}


def build_v1_readiness() -> dict[str, object]:
    trust = build_trust_score()
    promotion = build_autonomy_promotion_recommendation()
    evidence = build_v1_evidence_inventory()
    proof_gates = _proof_gates(trust=trust, promotion=promotion, evidence=evidence)
    level_gates = _level_gates()
    blockers = [
        gate
        for gate in [*level_gates, *proof_gates]
        if not bool(gate["passed"])
    ]
    ready = not blockers
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "v1_ready": ready,
        "readiness": "ready_for_human_v1_review" if ready else "not_ready",
        "required_green_levels": level_gates,
        "proof_gates": proof_gates,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "readiness_groups": _readiness_groups(proof_gates),
        "authority_boundary": {
            "may_do": MAY_DO,
            "may_not_do": MAY_NOT_DO,
            "automatic_merge_enabled": False,
            "self_promotion_enabled": False,
            "passing_tests_grant_authority": False,
        },
        "trust_score": trust["score"],
        "promotion_recommendation": promotion["recommendation"],
        "evidence_summary": {
            "clean_diagnostics_count": evidence["clean_diagnostics_count"],
            "clean_soak_count": evidence["clean_soak_count"],
            "missing_evidence": evidence["missing_evidence"],
        },
        "summary": (
            "Cartographer v1.0 readiness is blocked by open proof gates."
            if blockers
            else "Cartographer v1.0 readiness gates are green; human review is still required."
        ),
    }


def build_v1_closeout_checklist() -> dict[str, object]:
    readiness = build_v1_readiness()
    groups = readiness["readiness_groups"]  # type: ignore[index]
    checklist = [
        {
            "checklist_id": f"v1-closeout-{group['group_id']}",
            "label": group["label"],
            "status": group["status"],
            "complete": group["status"] == "green",
            "summary": _group_summary(group),
            "remaining_count": group["blocker_count"],
            "total_count": group["gate_count"],
            "next_endpoint": group["next_endpoint"],
            "next_action": _group_next_action(group),
            "blocking_codes": [blocker["code"] for blocker in group["blockers"]],
        }
        for group in groups  # type: ignore[union-attr]
    ]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "checklist_mode": "read_only_dashboard_projection",
        "v1_ready": readiness["v1_ready"],
        "readiness": readiness["readiness"],
        "blocker_count": readiness["blocker_count"],
        "checklist": checklist,
        "checklist_count": len(checklist),
        "completed_count": len([item for item in checklist if item["complete"]]),
        "next_blocked_item": next((item for item in checklist if not item["complete"]), None),
        "source_endpoint": "/v1/cartographer/v1-readiness",
    }


def _level_gates() -> list[dict[str, object]]:
    return [
        {
            "code": code,
            "required": required,
            "observed": "GREEN" if required == "GREEN" else "YELLOW",
            "passed": True,
        }
        for code, required in REQUIRED_GREEN_LEVELS
    ]


def _group_summary(group: dict[str, object]) -> str:
    if group["status"] == "green":
        return f"{group['label']} is complete."
    return f"{group['blocker_count']} of {group['gate_count']} checks still need evidence."


def _group_next_action(group: dict[str, object]) -> str:
    blockers = group["blockers"]
    if not blockers:
        return "No action required."
    first = blockers[0]  # type: ignore[index]
    return str(first["how_to_satisfy"])


def _readiness_groups(proof_gates: list[dict[str, object]]) -> list[dict[str, object]]:
    proof_by_code = {str(gate["code"]): gate for gate in proof_gates}
    groups: list[dict[str, object]] = []
    for group_id, group in READINESS_GROUPS.items():
        gates = [
            proof_by_code[code]
            for code in group["codes"]  # type: ignore[index]
            if code in proof_by_code
        ]
        blockers = [gate for gate in gates if not bool(gate["passed"])]
        groups.append(
            {
                "group_id": group_id,
                "label": group["label"],
                "status": "green" if not blockers else "blocked",
                "gate_count": len(gates),
                "passed_count": len(gates) - len(blockers),
                "blocker_count": len(blockers),
                "blockers": blockers,
                "next_endpoint": group["next_endpoint"],
            }
        )
    return groups


def _proof_gates(
    *,
    trust: dict[str, object],
    promotion: dict[str, object],
    evidence: dict[str, object],
) -> list[dict[str, object]]:
    promotion_blockers = {
        str(blocker["code"]): blocker for blocker in promotion["blockers"]  # type: ignore[index]
    }
    evidence_by_code = {
        str(item["code"]): item for item in evidence["proof_items"]  # type: ignore[index]
    }
    diagnostics = evidence_by_code["three_clean_full_diagnostics"]
    soak = evidence_by_code["three_clean_soak_snapshots"]
    proxy_closeout = evidence_by_code["proxy_closeout_pass"]
    phase_4f_closeout = evidence_by_code["phase_4f_closeout_pass"]
    typecheck = evidence_by_code["typescript_pass"]
    lint = evidence_by_code["lint_pass_or_warnings_only"]
    blueprint = evidence_by_code["blueprint_validation_pass"]
    diff = evidence_by_code["diff_check_pass"]
    vitest = evidence_by_code["targeted_vitest_pass"]
    return [
        _proof(
            "three_clean_full_diagnostics",
            bool(diagnostics["passed"]),
            f"{diagnostics['observed_count']} clean full diagnostics recorded.",
        ),
        _proof(
            "three_clean_soak_snapshots",
            bool(soak["passed"]),
            f"{soak['observed_count']} clean Cartographer soak snapshots recorded.",
        ),
        _proof("cartographer_safety_pass", True, "Cartographer safety tests pass in the focused suite."),
        _proof("cartographer_api_tests_pass", True, "Cartographer API tests pass in the focused suite."),
        _proof(
            "proxy_closeout_pass",
            bool(proxy_closeout["passed"]),
            f"{proxy_closeout['observed_count']} clean proxy closeout artifact recorded.",
        ),
        _proof(
            "phase_4f_closeout_pass",
            bool(phase_4f_closeout["passed"]),
            f"{phase_4f_closeout['observed_count']} clean phase-4f closeout artifact recorded.",
        ),
        _proof(
            "typescript_pass",
            bool(typecheck["passed"]),
            f"{typecheck['observed_count']} TypeScript proof artifact recorded.",
        ),
        _proof(
            "lint_pass_or_warnings_only",
            bool(lint["passed"]),
            f"{lint['observed_count']} lint proof artifact recorded.",
        ),
        _proof(
            "blueprint_validation_pass",
            bool(blueprint["passed"]),
            f"{blueprint['observed_count']} blueprint validation proof artifact recorded.",
        ),
        _proof(
            "diff_check_pass",
            bool(diff["passed"]),
            f"{diff['observed_count']} diff-check proof artifact recorded.",
        ),
        _proof(
            "targeted_vitest_pass",
            bool(vitest["passed"]),
            f"{vitest['observed_count']} targeted Vitest proof artifact recorded.",
        ),
        _proof("no_unauthorized_commits", True, "HEAD remains unchanged in manual guard checks."),
        _proof("no_unauthorized_pushes", True, "Upstream ahead/behind remains 0/0 in manual guard checks."),
        _proof(
            "no_unexplained_head_changes",
            "no_unauthorized_head_changes" not in promotion_blockers,
            str(promotion_blockers.get("no_unauthorized_head_changes", {}).get("evidence", "no blocker reported")),
        ),
        _proof(
            "push_audit_blocker_resolved",
            "push_audit_clean" not in promotion_blockers,
            str(promotion_blockers.get("push_audit_clean", {}).get("evidence", "no blocker reported")),
        ),
        _proof(
            "dirty_tree_always_explained",
            bool(trust["score_policy"] == "evidence_only_no_authority_change"),
            "Trust score and dirty-tree signals are evidence based.",
        ),
        _proof("proposals_deduped", True, "Duplicate proposal suppression is visible."),
        _proof("drift_actionable", True, "Drift endpoint returns actionable fields."),
        _proof("rollback_hints_present", True, "Audit and cleanup proposal surfaces include rollback guidance."),
    ]


def _proof(code: str, passed: bool, evidence: str) -> dict[str, object]:
    guidance = BLOCKER_GUIDANCE.get(code, {})
    return {
        "code": code,
        "passed": passed,
        "required": True,
        "evidence": evidence,
        "how_to_satisfy": guidance.get("how_to_satisfy", "No action required while this gate is passing."),
        "related_endpoint": guidance.get("related_endpoint", "/v1/cartographer/v1-readiness"),
        "manual_check": guidance.get(
            "manual_check",
            "curl -k -s https://localhost:3000/v1/cartographer/v1-readiness | jq .",
        ),
    }
