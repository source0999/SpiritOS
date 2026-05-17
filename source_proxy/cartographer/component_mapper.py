from __future__ import annotations

from fnmatch import fnmatchcase

from source_proxy.cartographer.models import ComponentMapping, UnmappedPath


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "blocked": 3, "unknown": 4}

COMPONENT_RULES: tuple[ComponentMapping, ...] = (
    ComponentMapping(
        component_id="cartographer",
        label="Cartographer",
        paths=["source_proxy/cartographer/**"],
        blueprint_id="cartographer-agent",
        risk="medium",
    ),
    ComponentMapping(
        component_id="cartographer-api-bridge",
        label="Cartographer API bridge",
        paths=["src/app/v1/cartographer/**"],
        blueprint_id="cartographer-agent",
        risk="medium",
    ),
    ComponentMapping(
        component_id="coding-workflow",
        label="Coding workflow",
        paths=["src/app/v1/coding/**", "src/components/coding/**"],
        blueprint_id="dashboard-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="scout-dashboard-bridge",
        label="Scout dashboard bridge",
        paths=["src/app/api/scout/**"],
        blueprint_id="system-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="scout",
        label="Scout",
        paths=["scout/**"],
        blueprint_id="system-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="source-proxy",
        label="Source Proxy",
        paths=["source_proxy/**"],
        blueprint_id="system-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="dashboard",
        label="Dashboard",
        paths=["src/components/dashboard/**", "src/app/(dashboard)/**"],
        blueprint_id="dashboard-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="chat-workspace",
        label="Chat workspace",
        paths=["src/app/chat/**", "src/components/chat/**", "src/hooks/useSpirit*"],
        blueprint_id="chat-workspace",
        risk="medium",
    ),
    ComponentMapping(
        component_id="oracle",
        label="Oracle",
        paths=["src/app/oracle/**", "src/components/oracle/**"],
        blueprint_id="oracle-voice",
        risk="medium",
    ),
    ComponentMapping(
        component_id="windows-desktop-agent",
        label="Windows desktop agent",
        paths=["scripts/spiritdesktop-windows/**"],
        blueprint_id="system-state",
        risk="medium",
    ),
    ComponentMapping(
        component_id="blueprint-system",
        label="Blueprint system",
        paths=["_blueprints/**"],
        blueprint_id="blueprint-index",
        risk="low",
    ),
    ComponentMapping(
        component_id="docs",
        label="Docs",
        paths=["docs/**", "README.md"],
        blueprint_id="system-state",
        risk="low",
    ),
    ComponentMapping(
        component_id="design-demo",
        label="Design demo",
        paths=["src/app/design-demo/**", "src/components/design-demo/**"],
        blueprint_id="design-demo",
        risk="medium",
        sandbox=True,
    ),
)


def component_rules() -> list[ComponentMapping]:
    return list(COMPONENT_RULES)


def map_paths(paths: list[str]) -> tuple[list[ComponentMapping], list[UnmappedPath]]:
    matched_by_component: dict[str, ComponentMapping] = {}
    unmapped: list[UnmappedPath] = []

    for raw_path in paths:
        normalized_path = _normalize_repo_path(raw_path)
        path_risk = _risk_for_path(normalized_path)
        if path_risk == "blocked":
            unmapped.append(
                UnmappedPath(
                    path="[redacted]",
                    reason="blocked_sensitive_or_outside_path",
                    risk="blocked",
                )
            )
            continue

        rule = _rule_for_path(normalized_path)
        if not rule:
            unmapped.append(
                UnmappedPath(
                    path=normalized_path,
                    reason="no_component_mapping_rule",
                    risk=path_risk,
                )
            )
            continue

        existing = matched_by_component.get(rule.component_id)
        matched_paths = [
            *(existing.matched_paths if existing else []),
            normalized_path,
        ]
        matched_path_risks = {
            **(existing.matched_path_risks if existing else {}),
            normalized_path: path_risk,
        }
        matched_by_component[rule.component_id] = ComponentMapping(
            component_id=rule.component_id,
            label=rule.label,
            paths=rule.paths,
            blueprint_id=rule.blueprint_id,
            matched_paths=matched_paths,
            risk=_max_risk([rule.risk, *(matched_path_risks.values())]),
            matched_path_risks=matched_path_risks,
            sandbox=rule.sandbox,
        )

    return list(matched_by_component.values()), unmapped


def build_component_map(sample_paths: list[str] | None = None) -> dict[str, object]:
    if sample_paths is None:
        return {
            "components": component_rules(),
            "unmapped_paths": [],
            "mapping_mode": "rules",
        }

    components, unmapped = map_paths(sample_paths)
    return {
        "components": components,
        "unmapped_paths": unmapped,
        "mapping_mode": "sample_paths",
    }


def _rule_for_path(path: str) -> ComponentMapping | None:
    for rule in COMPONENT_RULES:
        if any(_matches_pattern(path, pattern) for pattern in rule.paths):
            return rule
    return None


def _matches_pattern(path: str, pattern: str) -> bool:
    normalized_pattern = _normalize_repo_path(pattern)
    if normalized_pattern.endswith("/**"):
        prefix = normalized_pattern[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatchcase(path, normalized_pattern)


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _risk_for_path(path: str) -> str:
    lowered = path.lower()
    segments = [segment for segment in lowered.split("/") if segment]

    if (
        ".." in segments
        or lowered.startswith("/")
        or lowered.startswith("~")
        or any(segment.startswith(".env") for segment in segments)
        or any(segment in {"private", "secrets", "tokens", "credentials"} for segment in segments)
        or lowered.endswith(".pem")
        or lowered.endswith(".key")
    ):
        return "blocked"

    if (
        "approval" in lowered
        or "apply" in lowered
        or "commit" in lowered
        or "push" in lowered
        or "secret" in lowered
        or "token" in lowered
        or "credential" in lowered
        or "sandbox" in lowered
        or "filesystem" in lowered
        or "safety" in lowered
        or lowered.endswith(".env")
    ):
        return "high"

    if (
        lowered.startswith("docs/")
        or lowered == "readme.md"
        or lowered.startswith("_blueprints/")
        or "/runbooks/" in lowered
        or "/tests/" in lowered
        or lowered.endswith(".test.ts")
        or lowered.endswith("_test.py")
        or lowered.startswith("source_proxy/tests/")
    ):
        return "low"

    if (
        lowered.startswith("src/components/dashboard/")
        or lowered.startswith("src/components/coding/")
        or lowered.startswith("src/app/")
        or lowered.startswith("source_proxy/")
        or lowered.startswith("scout/")
        or lowered.startswith("scripts/spiritdesktop-windows/")
    ):
        return "medium"

    return "unknown"


def _max_risk(risks: list[str]) -> str:
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, RISK_ORDER["unknown"]))
