# Campaign 1 Duplicate-Path Inventory

Schema: `spiritos-campaign-1-duplicate-path-inventory/v1`  
Checkpoint: `edf29096cc0fe003684e91f0c33b9109e17f6781`

| Candidate | Classification | Canonical owner / disposition |
| --- | --- | --- |
| `/coding` shell | canonical production path | `CodingCockpitShell.tsx` owns the production lifecycle. |
| `/design-demo/coding` | compatibility delegator | Route preserves compatibility by delegating to `/coding`; removal candidate after deprecation window. |
| Chat coding surface | compatibility delegator | `SpiritTrinityChatShell` presents constrained canonical cockpit; no separate authority. |
| `labs/coding/CodingAgentInterface.tsx` | labs-only implementation | No production import, mount, or navigation. |
| `labs/coding/CodingCommandCenterShell.tsx` | labs-only implementation | No production import, mount, or navigation. |
| TS target-plugin registry | canonical production path | `src/lib/coding/target-plugins/index.ts` is browser transport/presentation entry point. |
| Python target adapter | canonical production path | `source_proxy/target_plugins/adapter.py` resolves identity, command, task spec, and evidence identity. |
| LumaCart Prompt/Coder fixtures, grader, probe | target-plugin implementation | TS plugin-owned; generic cockpit does not name DOM/grader/fixture details. |
| Python LumaCart diff builders | canonical executor port | `source_proxy/tasks/long_running.py` is reachable only through the resolved adapter in production; direct calls are test fixtures. |
| `verification/diff.py` fixture checks | defense in depth | Generic diff verifier enforces the isolated fixture contract; it does not resolve/select a target. |
| fixture reset route | compatibility delegator | Next body-preserving wrapper delegates to Source Proxy; resolved Prompt 1 identity gates mutation. |
| Cartographer route registrations | canonical production path | AST authority validator rejects duplicate method/path registrations; legacy mutation routes fail closed. |
| agent-trial scripts | test fixture / harness | Scripts under `scripts/agent-trials/` are not imported by production surfaces. |
| gallery/archive producers | archive producer | `/mnt/spirit-8tb/migration-evidence/...` is canonical bulk evidence; Git retains only receipt/manifests. |

## Removed duplicates

- `source_proxy/api/decision.py` no longer contains the three independent Prompt 1–3 mode classifiers. The resolved adapter is the sole selector.
- The three decision-route task-spec factories were removed in `489f3737`; adapter-owned task specs attach the resolved evidence identity.

## Static proof

- `npm run campaign-1:validate-authority` rejects production legacy shell imports/mounts and duplicate Cartographer registrations.
- `git ls-files docs/evidence scripts/media/model_gallery` returns zero paths; the archived evidence manifests retain byte-compare, readability, secret-scan, and rollback records.
- `source_proxy/tests/test_coding_regression_pack.py` covers the selected Coder path; direct executor entry points are test-only seams, not production route callers.
