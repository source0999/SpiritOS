from __future__ import annotations

from source_proxy.cartographer.autopilot_soak import build_docs_autopilot_soak_report
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import TrustScoreSignal
from source_proxy.cartographer.project_health import build_project_health
from source_proxy.cartographer.proposals import proposal_visibility_summary


def build_trust_score() -> dict[str, object]:
    signals = _signals()
    score = max(0, min(100, 85 + sum(signal.score_delta for signal in signals)))
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "authority_change_allowed": False,
        "actions_taken": False,
        "score": score,
        "grade": _grade(score),
        "signals": signals,
        "signal_count": len(signals),
        "explanation": _explanation(score, signals),
        "recommendations": _recommendations(signals),
        "score_policy": "evidence_only_no_authority_change",
    }


def _signals() -> list[TrustScoreSignal]:
    health = build_project_health()
    git_statuses = read_git_statuses()
    proposal_summary = proposal_visibility_summary()
    drift = detect_blueprint_drift()
    soak = build_docs_autopilot_soak_report()

    dirty_files = sorted(
        {
            path
            for project in health
            for path in getattr(project, "changed_files", [])
        }
    )
    unsafe_dirty_files = [
        path
        for project in health
        for path in getattr(project, "unsafe_dirty_files", [])
    ]
    unaudited_head_changes = [
        project.project_id for project in health if getattr(project, "unaudited_head_change", False)
    ]
    push_audit_failures = [
        project.project_id
        for project in health
        if str(getattr(project, "push_audit_status", "")) in {"missing", "failed"}
        and bool(getattr(project, "commits_to_push", []))
    ]
    duplicate_count = int(proposal_summary["duplicate_proposals_suppressed"])
    drift_count = len(drift)
    soak_green = soak["soak_grade"] == "green"
    safety_locked = all(not status.needs_push for status in git_statuses) or not push_audit_failures

    return [
        _signal(
            code="dirty_tree_explained",
            label="Dirty tree is visible",
            passed=True,
            score_delta=0 if dirty_files else 5,
            evidence=[f"dirty files: {len(dirty_files)}"],
        ),
        _signal(
            code="unsafe_dirty_files",
            label="Unsafe dirty paths",
            passed=not unsafe_dirty_files,
            score_delta=-15 if unsafe_dirty_files else 5,
            evidence=unsafe_dirty_files[:10] or ["no unsafe dirty files reported"],
        ),
        _signal(
            code="unauthorized_head_changes",
            label="Unauthorized HEAD changes",
            passed=not unaudited_head_changes,
            score_delta=-20 if unaudited_head_changes else 5,
            evidence=unaudited_head_changes or ["no unaudited HEAD changes reported"],
        ),
        _signal(
            code="push_audit",
            label="Push audit state",
            passed=not push_audit_failures,
            score_delta=-15 if push_audit_failures else 5,
            evidence=push_audit_failures or ["no push audit failures for queued commits"],
        ),
        _signal(
            code="duplicate_proposals",
            label="Duplicate proposal pressure",
            passed=duplicate_count == 0,
            score_delta=-5 * duplicate_count,
            evidence=[f"duplicates suppressed: {duplicate_count}"],
        ),
        _signal(
            code="drift_backlog",
            label="Drift backlog",
            passed=drift_count == 0,
            score_delta=-3 * drift_count,
            evidence=[f"drift findings: {drift_count}"],
        ),
        _signal(
            code="docs_autopilot_soak",
            label="Docs autopilot soak",
            passed=soak_green,
            score_delta=5 if soak_green else 0,
            evidence=[
                f"soak grade: {soak['soak_grade']}",
                f"observed days: {soak['observed_days']}",
            ],
        ),
        _signal(
            code="authority_locked",
            label="Authority remains locked",
            passed=safety_locked,
            score_delta=5 if safety_locked else -20,
            evidence=["trust score does not grant apply, commit, push, cleanup, or promotion authority"],
        ),
    ]


def _signal(
    *,
    code: str,
    label: str,
    passed: bool,
    score_delta: int,
    evidence: list[str],
) -> TrustScoreSignal:
    return TrustScoreSignal(
        code=code,
        label=label,
        passed=passed,
        score_delta=score_delta,
        evidence=evidence,
    )


def _grade(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def _explanation(score: int, signals: list[TrustScoreSignal]) -> str:
    negative = [signal for signal in signals if signal.score_delta < 0]
    if not negative:
        return f"Trust score is {score} because all tracked safety signals are neutral or positive."
    reasons = ", ".join(signal.label for signal in negative)
    return f"Trust score is {score}; deductions came from: {reasons}."


def _recommendations(signals: list[TrustScoreSignal]) -> list[str]:
    recommendations = [
        "Keep authority locked; trust score is advisory only.",
    ]
    if any(signal.code == "unsafe_dirty_files" and not signal.passed for signal in signals):
        recommendations.append("Review unsafe dirty files before approving cleanup, apply, commit, or push.")
    if any(signal.code == "drift_backlog" and not signal.passed for signal in signals):
        recommendations.append("Resolve or intentionally defer drift findings before raising autonomy.")
    if any(signal.code == "docs_autopilot_soak" and not signal.passed for signal in signals):
        recommendations.append("Continue soak until repeated clean evidence is available.")
    return recommendations
