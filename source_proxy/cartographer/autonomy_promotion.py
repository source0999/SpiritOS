from __future__ import annotations

from source_proxy.cartographer.autopilot_soak import build_docs_autopilot_soak_report
from source_proxy.cartographer.trust_score import build_trust_score


def build_autonomy_promotion_recommendation() -> dict[str, object]:
    trust = build_trust_score()
    signals = {
        str(signal.code): signal
        for signal in trust["signals"]  # type: ignore[index]
    }
    soak = build_docs_autopilot_soak_report()
    level_1_readiness = _level_1_readiness(trust=trust, soak=soak)
    gates = [
        _gate(
            "trust_score_high_enough",
            int(trust["score"]) >= 90,
            f"trust score: {trust['score']}",
        ),
        _gate(
            "clean_diagnostics_streak",
            False,
            "clean diagnostics streak is not yet recorded at 5",
        ),
        _gate(
            "no_dirty_unexplained_state",
            signals["dirty_tree_explained"].passed and signals["unsafe_dirty_files"].passed,
            "; ".join(signals["unsafe_dirty_files"].evidence),
        ),
        _gate(
            "no_unauthorized_head_changes",
            signals["unauthorized_head_changes"].passed,
            "; ".join(signals["unauthorized_head_changes"].evidence),
        ),
        _gate(
            "push_audit_clean",
            signals["push_audit"].passed,
            "; ".join(signals["push_audit"].evidence),
        ),
        _gate(
            "passing_soak",
            soak["soak_grade"] == "green",
            f"soak grade: {soak['soak_grade']}; observed days: {soak['observed_days']}",
        ),
        _gate(
            "authority_locked",
            not bool(trust["authority_granted"]) and not bool(trust["authority_change_allowed"]),
            "trust score and promotion gates do not grant authority",
        ),
    ]
    blockers = [gate for gate in gates if not gate["passed"]]
    recommended = not blockers
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "promotion_enabled": False,
        "authority_change_allowed": False,
        "actions_taken": False,
        "current_level": 5,
        "target_level": 6,
        "recommended": recommended,
        "recommendation": "ready_for_human_review" if recommended else "do_not_promote_yet",
        "requires_human_approval": True,
        "cannot_self_promote": True,
        "level_1_readiness": level_1_readiness,
        "level_1_recommendation": level_1_readiness["label"],
        "level_1_readiness_score": level_1_readiness["score"],
        "level_1_authority_granted": False,
        "level_1_enablement_allowed": False,
        "gate_count": len(gates),
        "gates": gates,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "trust_score": trust["score"],
        "trust_grade": trust["grade"],
        "reason": (
            "All gates are green; human approval is still required."
            if recommended
            else "One or more autonomy promotion gates are not green."
        ),
    }


def _level_1_readiness(*, trust: dict[str, object], soak: dict[str, object]) -> dict[str, object]:
    authority_locked = not bool(trust["authority_granted"]) and not bool(trust["authority_change_allowed"])
    checks = [
        _gate("v1_freeze_valid", True, "V1 freeze evidence is represented by read-only readiness checks."),
        _gate(
            "latest_soak_pass",
            soak["soak_grade"] == "green",
            f"soak grade: {soak['soak_grade']}; observed days: {soak['observed_days']}",
        ),
        _gate("apply_disabled", True, "Level 1 cannot apply files."),
        _gate("commit_disabled", True, "Level 1 cannot create commits."),
        _gate("push_disabled", True, "Level 1 cannot push."),
        _gate("approval_bypass_disabled", authority_locked, "Trust and promotion gates do not grant bypass authority."),
        _gate("docs_only_candidate_filters_valid", True, "Level 1 review is docs/evidence only."),
        _gate("kill_switch_visible", "autopilot_kill_switch" in soak, "Docs autopilot kill switch is visible."),
        _gate("daily_cap_visible", "docs_autopilot_daily_cap" in soak, "Docs autopilot daily cap is visible."),
        _gate("rollback_hints_present", True, "Rollback remains manual review guidance only."),
    ]
    blockers = [check for check in checks if not check["passed"]]
    score = int(round(100 * (len(checks) - len(blockers)) / len(checks)))
    label = "ready_for_level_1_review" if not blockers else "watch"
    return {
        "status": "observing",
        "level": 1,
        "mode": "read_only_readiness_review",
        "label": label,
        "score": score,
        "authority_granted": False,
        "enablement_allowed": False,
        "write_actions_enabled": False,
        "actions_taken": False,
        "operator_review_required": True,
        "checks": checks,
        "check_count": len(checks),
        "passed_count": len(checks) - len(blockers),
        "blockers": blockers,
        "blocker_count": len(blockers),
    }


def _gate(code: str, passed: bool, evidence: str) -> dict[str, object]:
    return {
        "code": code,
        "passed": passed,
        "evidence": evidence,
        "required": True,
    }
