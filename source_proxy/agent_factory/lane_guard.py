"""Deterministic lane checks for supplied file lists."""

from __future__ import annotations

from fnmatch import fnmatchcase

from source_proxy.agent_factory.contracts import (
    AuditFinding,
    EvidenceReference,
    LaneReport,
    LaneScope,
)


def evaluate_lane(
    scope: LaneScope,
    *,
    proposed_files: tuple[str, ...] = (),
    dirty_files: tuple[str, ...] = (),
) -> LaneReport:
    """Check proposed and dirty files against a supplied lane scope."""

    findings: list[AuditFinding] = []
    allowed = tuple(_normalize(path) for path in scope.allowed_files)
    forbidden = tuple(_normalize(path) for path in scope.forbidden_files)
    proposed = tuple(_normalize(path) for path in proposed_files)
    dirty = tuple(_normalize(path) for path in dirty_files)

    for path in proposed:
        if _matches(path, forbidden):
            findings.append(
                AuditFinding(
                    rule="forbidden_file",
                    severity="blocked",
                    subject=path,
                    detail="Proposed file is forbidden by supplied lane scope.",
                    evidence=EvidenceReference(
                        file=path,
                        source="proposed_files",
                        rule="forbidden_file",
                        detail=path,
                    ),
                )
            )
        if not _matches(path, allowed):
            findings.append(
                AuditFinding(
                    rule="outside_allowed_files",
                    severity="blocked",
                    subject=path,
                    detail="Proposed file is outside supplied allowed files.",
                    evidence=EvidenceReference(
                        file=path,
                        source="proposed_files",
                        rule="outside_allowed_files",
                        detail=path,
                    ),
                )
            )

    for path in dirty:
        if _matches(path, forbidden):
            findings.append(
                AuditFinding(
                    rule="forbidden_dirty_file",
                    severity="blocked",
                    subject=path,
                    detail="Dirty file is in a forbidden file family or path.",
                    evidence=EvidenceReference(
                        file=path,
                        source="dirty_files",
                        rule="forbidden_dirty_file",
                        detail=path,
                    ),
                )
            )
        elif not _matches(path, allowed):
            findings.append(
                AuditFinding(
                    rule="dirty_file_outside_lane",
                    severity="caution",
                    subject=path,
                    detail=(
                        "Dirty file was supplied outside this lane; Agent Factory "
                        "does not claim, clean, or modify it."
                    ),
                    evidence=EvidenceReference(
                        file=path,
                        source="dirty_files",
                        rule="dirty_file_outside_lane",
                        detail=path,
                    ),
                )
            )

    findings.extend(_family_overlap_findings(scope, proposed))
    return LaneReport.from_findings(tuple(findings))


def _family_overlap_findings(
    scope: LaneScope, proposed_files: tuple[str, ...]
) -> list[AuditFinding]:
    matched_families: dict[str, list[str]] = {}
    normalized_families = {
        family: tuple(_normalize(pattern) for pattern in patterns)
        for family, patterns in scope.file_families.items()
    }

    for path in proposed_files:
        for family, patterns in normalized_families.items():
            if _matches(path, patterns):
                matched_families.setdefault(family, []).append(path)

    if len(matched_families) <= 1:
        return []

    families = ", ".join(sorted(matched_families))
    files = ", ".join(sorted({path for paths in matched_families.values() for path in paths}))
    return [
        AuditFinding(
            rule="file_family_overlap",
            severity="caution",
            subject=families,
            detail=f"Proposed files span multiple supplied file families: {files}.",
            evidence=EvidenceReference(
                source="proposed_files",
                rule="file_family_overlap",
                detail=files,
            ),
        )
    ]


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(_matches_one(path, pattern) for pattern in patterns)


def _matches_one(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    if any(token in pattern for token in "*?[]"):
        return fnmatchcase(path, pattern)
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return path == pattern


def _normalize(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")
