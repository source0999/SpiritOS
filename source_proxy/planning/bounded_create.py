from __future__ import annotations

import re

from source_proxy.planning.plan import CoderPacket
from source_proxy.safety.paths import normalize_repo_path_candidate

BOUNDED_CREATE_STYLE_MARKER = "bounded_proposal_create"


def packet_is_bounded_proposal_create(packet: CoderPacket) -> bool:
    if packet.operation != "create":
        return False
    directives = [str(item).strip().lower() for item in packet.style_directives]
    return BOUNDED_CREATE_STYLE_MARKER in directives


def bounded_create_replacement_content(target_path: str, task: str = "") -> str | None:
    normalized = normalize_repo_path_candidate(target_path)
    if not normalized:
        return None
    known = _KNOWN_PAGE_SCAFFOLDS.get(normalized)
    if known is not None:
        return known
    if not normalized.endswith("/page.tsx"):
        return None
    return _scaffold_from_app_page_path(normalized, task)


_KNOWN_PAGE_SCAFFOLDS: dict[str, str] = {
    "src/app/proxy-backend/page.tsx": (
        'import CodingAgentInterface from "@/components/coding/CodingAgentInterface";\n'
        "\n"
        "export default function ProxyBackendPage() {\n"
        "  return (\n"
        '    <main className="min-h-dvh bg-slate-950">\n'
        "      <CodingAgentInterface />\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
}


def _scaffold_from_app_page_path(target_path: str, task: str) -> str | None:
    match = re.match(r"^src/app/([^/]+)/page\.tsx$", target_path)
    if not match:
        return None
    segment = match.group(1)
    if segment.startswith("("):
        return None
    component = _route_segment_to_component_name(segment)
    task_normalized = task.lower().replace(" ", "")
    if "codingagentinterface" in task_normalized:
        import_line = 'import CodingAgentInterface from "@/components/coding/CodingAgentInterface";'
        body = "<CodingAgentInterface />"
    else:
        import_line = ""
        body = f"<div>{component}</div>"
    lines: list[str] = []
    if import_line:
        lines.extend([import_line, ""])
    lines.extend(
        [
            f"export default function {component}() {{",
            "  return (",
            '    <main className="min-h-dvh bg-slate-950">',
            f"      {body}",
            "    </main>",
            "  );",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _route_segment_to_component_name(segment: str) -> str:
    parts = re.split(r"[-_]+", segment.strip())
    base = "".join(p[:1].upper() + p[1:] for p in parts if p)
    return f"{base}Page" if base else "Page"
