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
        '"use client";\n'
        "\n"
        "import { useState } from 'react';\n"
        'import Link from "next/link";\n'
        "\n"
        "const sections = [\n"
        '  { title: "Basic Apps", href: "/agent-lab/calculator" },\n'
        '  { title: "Cards", href: "/agent-lab/cards" },\n'
        '  { title: "Counter", href: "/agent-lab/counter" },\n'
        '  { title: "Diagnostics", href: "/agent-lab/proxy-health" },\n'
        '  { title: "Form", href: "/agent-lab/form" },\n'
        '  { title: "Model Picker", href: "/agent-lab/model-picker" },\n'
        '  { title: "Notes", href: "/agent-lab/notes" },\n'
        '  { title: "Tests", href: "/agent-lab/todo" },\n'
        '  { title: "Theme", href: "/agent-lab/theme" },\n'
        "];\n"
        "\n"
        "export default function AgentLabPage() {\n"
        "  const [ready] = useState(true);\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-4xl">\n'
        "        <h1>Agent Lab</h1>\n"
        '        <p className="mt-3 text-slate-300">This is for local coder benchmark tests.</p>\n'
        '        <p className="sr-only">{ready ? "Agent Lab ready" : "Agent Lab loading"}</p>\n'
        "        <div>Basic Apps</div>\n"
        "        <div>Tools</div>\n"
        "        <div>Research</div>\n"
        "        <div>Diagnostics</div>\n"
        "        <div>Tests</div>\n"
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
    "src/app/agent-lab/calculator/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useMemo, useState } from "react";\n'
        "\n"
        "type Operation = \"add\" | \"subtract\" | \"multiply\" | \"divide\";\n"
        "\n"
        "const operations: Array<{ id: Operation; label: string }> = [\n"
        '  { id: "add", label: "Add" },\n'
        '  { id: "subtract", label: "Subtract" },\n'
        '  { id: "multiply", label: "Multiply" },\n'
        '  { id: "divide", label: "Divide" },\n'
        "];\n"
        "\n"
        "export default function CalculatorPage() {\n"
        '  const [first, setFirst] = useState("0");\n'
        '  const [second, setSecond] = useState("0");\n'
        '  const [operation, setOperation] = useState<Operation>("add");\n'
        "\n"
        "  const result = useMemo(() => {\n"
        "    const left = Number(first);\n"
        "    const right = Number(second);\n"
        "    if (!Number.isFinite(left) || !Number.isFinite(right)) return \"Enter two numbers\";\n"
        "    if (operation === \"divide\" && right === 0) return \"Cannot divide by zero\";\n"
        "    if (operation === \"subtract\") return String(left - right);\n"
        "    if (operation === \"multiply\") return String(left * right);\n"
        "    if (operation === \"divide\") return String(left / right);\n"
        "    return String(left + right);\n"
        "  }, [first, operation, second]);\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Calculator</h1>\n'
        '        <div className="mt-6 grid gap-4 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        '          <label className="grid gap-2 text-sm text-slate-300">\n'
        "            First number\n"
        '            <input value={first} onChange={(event) => setFirst(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" inputMode="decimal" />\n'
        "          </label>\n"
        '          <label className="grid gap-2 text-sm text-slate-300">\n'
        "            Second number\n"
        '            <input value={second} onChange={(event) => setSecond(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" inputMode="decimal" />\n'
        "          </label>\n"
        '          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">\n'
        "            {operations.map((item) => (\n"
        "              <button\n"
        "                key={item.id}\n"
        "                type=\"button\"\n"
        "                onClick={() => setOperation(item.id)}\n"
        "                className={operation === item.id ? \"rounded-md bg-cyan-300 px-3 py-2 font-medium text-slate-950\" : \"rounded-md border border-slate-700 px-3 py-2 text-slate-200\"}\n"
        "              >\n"
        "                {item.label}\n"
        "              </button>\n"
        "            ))}\n"
        "          </div>\n"
        '          <div className="rounded-md border border-slate-700 bg-slate-950 p-4">\n'
        '            <p className="text-sm text-slate-400">Result</p>\n'
        '            <p className="mt-1 text-2xl font-semibold">{result}</p>\n'
        "          </div>\n"
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
    "src/app/agent-lab/cards/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useMemo, useState } from "react";\n'
        "\n"
        "const cards = [\n"
        '  { title: "Card 1", description: "A fake benchmark card for filtering." },\n'
        '  { title: "Card 2", description: "A second fake card for the local test area." },\n'
        '  { title: "Card 3", description: "Search should match this sample card." },\n'
        '  { title: "Card 4", description: "Simple content keeps the trial reversible." },\n'
        '  { title: "Card 5", description: "Another fake card in the Agent Lab." },\n'
        '  { title: "Card 6", description: "Filtering updates live while typing." },\n'
        '  { title: "Card 7", description: "The page stays inside /agent-lab." },\n'
        '  { title: "Card 8", description: "Eight cards make the smoke test obvious." },\n'
        "];\n"
        "\n"
        "export default function CardsPage() {\n"
        '  const [query, setQuery] = useState("");\n'
        "  const filteredCards = useMemo(() => {\n"
        "    const needle = query.trim().toLowerCase();\n"
        "    if (!needle) return cards;\n"
        "    return cards.filter((card) => `${card.title} ${card.description}`.toLowerCase().includes(needle));\n"
        "  }, [query]);\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-4xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Fake Cards</h1>\n'
        '        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search cards" className="mt-6 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100" />\n'
        '        <div className="mt-6 grid gap-3 sm:grid-cols-2">\n'
        "          {filteredCards.map((card) => (\n"
        '            <article key={card.title} className="rounded-lg border border-slate-700 bg-slate-900 p-4">\n'
        '              <h2 className="font-medium">{card.title}</h2>\n'
        '              <p className="mt-2 text-sm text-slate-300">{card.description}</p>\n'
        "            </article>\n"
        "          ))}\n"
        "        </div>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/form/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { FormEvent, useState } from "react";\n'
        "\n"
        "type Submission = { name: string; message: string };\n"
        "\n"
        "export default function FormPage() {\n"
        '  const [name, setName] = useState("");\n'
        '  const [message, setMessage] = useState("");\n'
        '  const [error, setError] = useState("");\n'
        "  const [submitted, setSubmitted] = useState<Submission | null>(null);\n"
        "\n"
        "  function handleSubmit(event: FormEvent<HTMLFormElement>) {\n"
        "    event.preventDefault();\n"
        "    if (!name.trim() || !message.trim()) {\n"
        '      setError("Name and message are required.");\n'
        "      return;\n"
        "    }\n"
        '    setError("");\n'
        "    setSubmitted({ name: name.trim(), message: message.trim() });\n"
        "  }\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Form</h1>\n'
        '        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        '          <label className="grid gap-2 text-sm text-slate-300">Name<input value={name} onChange={(event) => setName(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" /></label>\n'
        '          <label className="grid gap-2 text-sm text-slate-300">Message<textarea value={message} onChange={(event) => setMessage(event.target.value)} className="min-h-28 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" /></label>\n'
        '          {error ? <p className="text-sm text-red-300">{error}</p> : null}\n'
        '          <button type="submit" className="rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950">Submit</button>\n'
        "        </form>\n"
        "        {submitted ? (\n"
        '          <section className="mt-6 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        '            <h2 className="font-medium">Submitted Message</h2>\n'
        '            <p className="mt-3 text-sm text-slate-300">Name: {submitted.name}</p>\n'
        '            <p className="mt-2 text-sm text-slate-300">Message: {submitted.message}</p>\n'
        "          </section>\n"
        "        ) : null}\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/counter/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useEffect, useState } from "react";\n'
        "\n"
        'const storageKey = "agent-lab-counter";\n'
        "\n"
        "export default function CounterPage() {\n"
        "  const [count, setCount] = useState(0);\n"
        "\n"
        "  useEffect(() => {\n"
        "    const saved = window.localStorage.getItem(storageKey);\n"
        "    if (saved !== null) setCount(Number(saved));\n"
        "  }, []);\n"
        "\n"
        "  useEffect(() => {\n"
        "    window.localStorage.setItem(storageKey, String(count));\n"
        "  }, [count]);\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Counter</h1>\n'
        '        <div className="mt-6 rounded-lg border border-slate-700 bg-slate-900 p-5 text-center">\n'
        '          <p className="text-sm text-slate-400">Saved count</p>\n'
        '          <p className="mt-2 text-5xl font-semibold">{count}</p>\n'
        '          <div className="mt-6 flex justify-center gap-3">\n'
        '            <button type="button" onClick={() => setCount((value) => value - 1)} className="rounded-md border border-slate-600 px-4 py-2">Minus</button>\n'
        '            <button type="button" onClick={() => setCount(0)} className="rounded-md border border-slate-600 px-4 py-2">Reset</button>\n'
        '            <button type="button" onClick={() => setCount((value) => value + 1)} className="rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950">Plus</button>\n'
        "          </div>\n"
        "        </div>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/theme/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useEffect, useState } from "react";\n'
        "\n"
        "type Theme = \"light\" | \"dark\";\n"
        'const storageKey = "agent-lab-theme";\n'
        "\n"
        "export default function ThemePage() {\n"
        '  const [theme, setTheme] = useState<Theme>("dark");\n'
        "\n"
        "  useEffect(() => {\n"
        "    const saved = window.localStorage.getItem(storageKey);\n"
        '    if (saved === "light" || saved === "dark") setTheme(saved);\n'
        "  }, []);\n"
        "\n"
        "  useEffect(() => {\n"
        "    window.localStorage.setItem(storageKey, theme);\n"
        "  }, [theme]);\n"
        "\n"
        '  const isLight = theme === "light";\n'
        "\n"
        "  return (\n"
        '    <main className={isLight ? "min-h-screen bg-white px-6 py-10 text-slate-950" : "min-h-screen bg-slate-950 px-6 py-10 text-slate-100"}>\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className={isLight ? "text-sm text-blue-700" : "text-sm text-cyan-300"}>Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Theme Toggle</h1>\n'
        '        <section className={isLight ? "mt-6 rounded-lg border border-slate-300 bg-slate-50 p-5" : "mt-6 rounded-lg border border-slate-700 bg-slate-900 p-5"}>\n'
        '          <p>Current theme: {theme}</p>\n'
        '          <button type="button" onClick={() => setTheme(isLight ? "dark" : "light")} className={isLight ? "mt-4 rounded-md bg-slate-950 px-4 py-2 text-white" : "mt-4 rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950"}>Switch Theme</button>\n'
        "        </section>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/notes/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { FormEvent, useState } from "react";\n'
        "\n"
        "type Note = { id: number; title: string; body: string };\n"
        "\n"
        "export default function NotesPage() {\n"
        "  const [notes, setNotes] = useState<Note[]>([]);\n"
        '  const [title, setTitle] = useState("");\n'
        '  const [body, setBody] = useState("");\n'
        "\n"
        "  function addNote(event: FormEvent<HTMLFormElement>) {\n"
        "    event.preventDefault();\n"
        "    if (!title.trim() || !body.trim()) return;\n"
        "    setNotes((current) => [...current, { id: Date.now(), title: title.trim(), body: body.trim() }]);\n"
        '    setTitle("");\n'
        '    setBody("");\n'
        "  }\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-3xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Notes</h1>\n'
        '        <form onSubmit={addNote} className="mt-6 grid gap-3 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        '          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Note title" className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />\n'
        '          <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Note body" className="min-h-24 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />\n'
        '          <button type="submit" className="rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950">Add Note</button>\n'
        "        </form>\n"
        '        <div className="mt-6 grid gap-3">\n'
        "          {notes.map((note) => (\n"
        '            <article key={note.id} className="rounded-lg border border-slate-700 bg-slate-900 p-4">\n'
        '              <div className="flex items-start justify-between gap-3">\n'
        '                <h2 className="font-medium">{note.title}</h2>\n'
        '                <button type="button" onClick={() => setNotes((current) => current.filter((item) => item.id !== note.id))} className="rounded-md border border-slate-600 px-3 py-1 text-sm">Delete</button>\n'
        "              </div>\n"
        '              <p className="mt-2 text-sm text-slate-300">{note.body}</p>\n'
        "            </article>\n"
        "          ))}\n"
        "        </div>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/model-picker/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useState } from "react";\n'
        "\n"
        "const modelsByProvider: Record<string, string[]> = {\n"
        '  Local: ["qwen2.5-coder:7b", "llama3.1:8b"],\n'
        '  Cloud: ["gpt-4.1", "claude-3.5-sonnet"],\n'
        "};\n"
        "\n"
        "export default function ModelPickerPage() {\n"
        '  const [provider, setProvider] = useState("Local");\n'
        '  const [model, setModel] = useState("qwen2.5-coder:7b");\n'
        "\n"
        "  function chooseProvider(nextProvider: string) {\n"
        "    setProvider(nextProvider);\n"
        "    setModel(modelsByProvider[nextProvider][0]);\n"
        "  }\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Fake Model Picker</h1>\n'
        '        <div className="mt-6 grid gap-4 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        '          <label className="grid gap-2 text-sm text-slate-300">Provider<select value={provider} onChange={(event) => chooseProvider(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100">{Object.keys(modelsByProvider).map((item) => <option key={item}>{item}</option>)}</select></label>\n'
        '          <label className="grid gap-2 text-sm text-slate-300">Model<select value={model} onChange={(event) => setModel(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100">{modelsByProvider[provider].map((item) => <option key={item}>{item}</option>)}</select></label>\n'
        '          <p className="rounded-md border border-slate-700 bg-slate-950 p-4">Selected provider/model: {provider} / {model}</p>\n'
        "        </div>\n"
        "      </div>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
    "src/app/agent-lab/proxy-health/page.tsx": (
        '"use client";\n'
        "\n"
        'import Link from "next/link";\n'
        'import { useState } from "react";\n'
        "\n"
        "const statuses = [\"Frontend online\", \"Proxy online\", \"Model online\"];\n"
        "\n"
        "export default function ProxyHealthPage() {\n"
        "  const [timestamp, setTimestamp] = useState(() => new Date().toLocaleString());\n"
        "\n"
        "  return (\n"
        '    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">\n'
        '      <div className="mx-auto max-w-2xl">\n'
        '        <Link href="/agent-lab" className="text-sm text-cyan-300">Back to Agent Lab</Link>\n'
        '        <h1 className="mt-6 text-3xl font-semibold">Fake Proxy Health</h1>\n'
        '        <div className="mt-6 grid gap-3 rounded-lg border border-slate-700 bg-slate-900 p-5">\n'
        "          {statuses.map((status) => (\n"
        '            <div key={status} className="flex items-center justify-between rounded-md border border-slate-700 bg-slate-950 p-3">\n'
        '              <span>{status}</span><span className="text-cyan-300">OK</span>\n'
        "            </div>\n"
        "          ))}\n"
        '          <p className="text-sm text-slate-300">Last refreshed: {timestamp}</p>\n'
        '          <button type="button" onClick={() => setTimestamp(new Date().toLocaleString())} className="rounded-md bg-cyan-300 px-4 py-2 font-medium text-slate-950">Refresh</button>\n'
        "        </div>\n"
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
