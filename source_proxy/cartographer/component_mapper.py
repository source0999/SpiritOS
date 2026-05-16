from __future__ import annotations

from fnmatch import fnmatchcase

from source_proxy.cartographer.models import ComponentMapping, UnmappedPath


COMPONENT_RULES: tuple[ComponentMapping, ...] = (
    ComponentMapping(
        component_id="scout-dashboard-bridge",
        label="Scout dashboard bridge",
        paths=["src/app/api/scout/**"],
        blueprint_id="system-state",
    ),
    ComponentMapping(
        component_id="scout",
        label="Scout",
        paths=["scout/**"],
        blueprint_id="system-state",
    ),
    ComponentMapping(
        component_id="source-proxy",
        label="Source Proxy",
        paths=["source_proxy/**"],
        blueprint_id="system-state",
    ),
    ComponentMapping(
        component_id="dashboard",
        label="Dashboard",
        paths=["src/components/dashboard/**", "src/app/(dashboard)/**"],
        blueprint_id="dashboard-state",
    ),
    ComponentMapping(
        component_id="chat-workspace",
        label="Chat workspace",
        paths=["src/app/chat/**", "src/components/chat/**", "src/hooks/useSpirit*"],
        blueprint_id="chat-workspace",
    ),
    ComponentMapping(
        component_id="oracle",
        label="Oracle",
        paths=["src/app/oracle/**", "src/components/oracle/**"],
        blueprint_id="oracle-voice",
    ),
    ComponentMapping(
        component_id="windows-desktop-agent",
        label="Windows desktop agent",
        paths=["scripts/spiritdesktop-windows/**"],
        blueprint_id="system-state",
    ),
    ComponentMapping(
        component_id="blueprint-system",
        label="Blueprint system",
        paths=["_blueprints/**"],
        blueprint_id="blueprint-index",
    ),
    ComponentMapping(
        component_id="design-demo",
        label="Design demo",
        paths=["src/app/design-demo/**", "src/components/design-demo/**"],
        blueprint_id="design-demo",
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
        rule = _rule_for_path(normalized_path)
        if not rule:
            unmapped.append(UnmappedPath(path=normalized_path))
            continue

        existing = matched_by_component.get(rule.component_id)
        matched_paths = [
            *(existing.matched_paths if existing else []),
            normalized_path,
        ]
        matched_by_component[rule.component_id] = ComponentMapping(
            component_id=rule.component_id,
            label=rule.label,
            paths=rule.paths,
            blueprint_id=rule.blueprint_id,
            matched_paths=matched_paths,
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
    return path.strip().replace("\\", "/").lstrip("./")
