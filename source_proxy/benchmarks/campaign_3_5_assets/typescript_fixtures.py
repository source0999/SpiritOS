"""Seeded TypeScript and React starter repositories with real baseline states."""
from __future__ import annotations

import hashlib
from typing import Callable


def _tag(seed: str, fixture_id: str) -> str:
    return f"// fixture={fixture_id}; layout={hashlib.sha256(seed.encode('ascii')).hexdigest()[:10]}\n"


def _package(name: str) -> str:
    return '{"private":true,"name":"' + name + '","scripts":{"test":"node --test"}}\n'


def _node_small(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-node-small")
    return {"package.json": _package("ts-node-small"), "src/dates.ts": h + "export const renderUtc = (value: Date) => require('moment').utc(value).format();\n", "src/pagination.ts": "export function offset(page:number, pageSize:number) { return page * pageSize; } // baseline page-one bug\n", "src/server.ts": "export const jsonOptions = {}; // baseline lacks body limit\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.equal(1, 1);\n", "src/legacy_dates.ts": "export const renderUtc = () => 'decoy';\n"}


def _library_small(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-library-small")
    return {"package.json": _package("ts-library-small"), "src/security/redact.ts": h + "export function redactSecrets(value: unknown) { return value; } // baseline does not traverse\n", "src/jobs/create.ts": "import { randomUUID } from 'node:crypto'; export function createJob(name:string) { return {id: randomUUID(), name}; }\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "src/security/redact_test_helper.ts": "export const redactSecrets = (x:unknown) => x; // decoy\n"}


def _monorepo(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-monorepo")
    return {"package.json": _package("ts-monorepo"), "packages/shared/src/contracts.ts": h + "export type Invoice = { id:string; total:number };\n", "packages/api/src/invoices.ts": "export const exportInvoices = () => { throw new Error('not implemented'); };\n", "packages/worker/src/thumbnail.ts": "export async function processThumbnail() { return undefined; }\n", "packages/gateway/src/tracing.ts": "export const enqueue = (job:object) => job; // baseline drops trace context\n", "docs/feature-flags.md": "invoice_csv_export is declared but no route uses it.\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "packages/api/src/obsolete_export.ts": "export const exportInvoices = () => 'stale-decoy';\n"}


def _node_debug(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-node-debug")
    return {"package.json": _package("ts-node-debug"), "src/audit.ts": h + "export async function record(tx:any, entry:any) { return tx.insert('audit', entry); } // rolls back with business transaction\n", "src/watch.ts": "export function watchFileOnly(watcher:any, file:string) { watcher.watch(file); } // misses rename saves\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "src/watch_legacy.ts": "export const watch = () => undefined;\n"}


def _node_multifile(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-node-multifile")
    return {"package.json": _package("ts-node-multifile"), "src/graphql/orders.ts": h + "export async function orders(repo:any) { return (await repo.orders()).map((o:any) => ({...o, user: repo.user(o.userId)})); }\n", "src/repositories/users.ts": "export class Users { user(id:string) { return {id}; } }\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "docs/graphql.md": "Resolvers currently load users one by one.\n"}


def _api_ambiguous(seed: str) -> dict[str, str]:
    h = _tag(seed, "ts-api-ambiguous")
    return {"package.json": _package("ts-api-ambiguous"), "src/comments/route.ts": h + "export const listComments = () => ({items: []}); // baseline has no shared cursor contract\n", "src/shared/pagination.ts": "export type CursorPage<T> = { items:T[]; nextCursor?:string };\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "src/comments/page_number_example.ts": "// documentation-only decoy convention\n"}


def _react_small(seed: str) -> dict[str, str]:
    h = _tag(seed, "react-small")
    return {"package.json": _package("react-small"), "src/SettingsPanel.tsx": h + "import {useEffect} from 'react'; export function SettingsPanel(){ useEffect(()=>{ window.addEventListener('resize', ()=>{}); }); return null; }\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "src/LegacySettingsPanel.tsx": "export const LegacySettingsPanel=()=>null;\n"}


def _react_monorepo(seed: str) -> dict[str, str]:
    h = _tag(seed, "react-monorepo")
    return {"package.json": _package("react-monorepo"), "packages/app/src/App.tsx": h + "export const App=()=>null; // baseline lacks command palette\n", "packages/design/src/Dialog.tsx": "export const Dialog=({children}:any)=>children;\n", "packages/router/src/navigation.ts": "export const navigate=(path:string)=>path;\n", "docs/accessibility.md": "Keyboard conventions are documented for dialogs.\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n"}


def _react_debug(seed: str) -> dict[str, str]:
    h = _tag(seed, "react-debug")
    return {"package.json": _package("react-debug"), "src/projects/rename.ts": h + "export async function rename(client:any, id:string, name:string){ await client.rename(id,name); } // baseline never invalidates query\n", "src/projects/queries.ts": "export const projectKey=(id:string)=>['project',id];\n", "tests/basic.test.ts": "import assert from 'node:assert/strict'; assert.ok(true);\n", "src/projects/demoRename.ts": "export const rename=()=>undefined; // storybook decoy\n"}


TYPESCRIPT_FIXTURE_BUILDERS: dict[str, Callable[[str], dict[str, str]]] = {
    "ts-node-small": _node_small, "ts-library-small": _library_small, "ts-monorepo": _monorepo,
    "ts-node-debug": _node_debug, "ts-node-multifile": _node_multifile, "ts-api-ambiguous": _api_ambiguous,
    "react-small": _react_small, "react-monorepo": _react_monorepo, "react-debug": _react_debug,
}


def build_typescript_fixture(fixture_id: str, seed: str) -> dict[str, str]:
    return TYPESCRIPT_FIXTURE_BUILDERS[fixture_id](seed)
