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


def _gate(code: str, passed: bool, evidence: str) -> dict[str, object]:
    return {
        "code": code,
        "passed": passed,
        "evidence": evidence,
        "required": True,
    }
