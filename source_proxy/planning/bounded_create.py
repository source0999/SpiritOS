from __future__ import annotations

import re

from source_proxy.planning.plan import CoderPacket
from source_proxy.safety.paths import normalize_repo_path_candidate

BOUNDED_CREATE_STYLE_MARKER = "bounded_proposal_create"


def packet_is_bounded_proposal_create(packet: CoderPacket) -> bool:
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
    "src/app/agent-lab/page.tsx": (
        'import Link from "next/link";\n'
        "\n"
        "const sections = [\n"
        '  { title: "Basic apps", href: "/agent-lab/calculator" },\n'
        '  { title: "Tools", href: "/agent-lab/counter" },\n'
        '  { title: "Diagnostics", href: "/agent-lab/theme" },\n'
        '  { title: "Tests", href: "/agent-lab/todo" },\n'
        "];\n"
        "\n"
        "export default function AgentLabPage() {\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-4xl">\n'
        '        <h1 className="text-4xl font-semibold">Agent Lab</h1>\n'
        '        <p className="mt-3 text-slate-300">This is for local coder benchmark tests.</p>\n'
        '        <div className="mt-8 grid gap-4 sm:grid-cols-2">\n'
        "          {sections.map((section) => (\n"
        '            <Link key={section.title} href={section.href} className="rounded-lg border border-slate-700 bg-slate-900 p-5 hover:border-cyan-300">\n'
        '              <h2 className="text-lg font-medium">{section.title}</h2>\n'
        '            </Link>\n'
        "          ))}\n"
        "        </div>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/todo/page.tsx": (
        '"use client";\n'
        "\n"
        'import { useState } from "react";\n'
        'import Link from "next/link";\n'
        "\n"
        "type Task = { id: number; text: string; done: boolean };\n"
        "\n"
        "export default function TodoPage() {\n"
        "  const [tasks, setTasks] = useState<Task[]>([]);\n"
        '  const [newTask, setNewTask] = useState("");\n'
        "  function addTask() {\n"
        "    const text = newTask.trim();\n"
        "    if (!text) return;\n"
        "    setTasks((current) => [...current, { id: Date.now(), text, done: false }]);\n"
        '    setNewTask("");\n'
        "  }\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Todo List</h1>\n'
        '        <div className="mt-6 flex gap-2">\n'
        '          <input value={newTask} onChange={(event) => setNewTask(event.target.value)} placeholder="Add a task" className="min-w-0 flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2" />\n'
        '          <button type="button" onClick={addTask} className="rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950">Add</button>\n'
        "        </div>\n"
        '        <ul className="mt-6 space-y-3">\n'
        "          {tasks.map((task) => (\n"
        '            <li key={task.id} className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-900 p-3">\n'
        '              <input type="checkbox" checked={task.done} onChange={() => setTasks((current) => current.map((item) => item.id === task.id ? { ...item, done: !item.done } : item))} />\n'
        '              <span className={task.done ? "flex-1 text-slate-500 line-through" : "flex-1"}>{task.text}</span>\n'
        '              <button type="button" onClick={() => setTasks((current) => current.filter((item) => item.id !== task.id))} className="rounded-md border border-slate-600 px-3 py-1 text-sm">Delete</button>\n'
        "            </li>\n"
        "          ))}\n"
        "        </ul>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
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
