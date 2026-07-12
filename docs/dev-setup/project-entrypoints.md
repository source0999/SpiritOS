# Project Entry Points

Read the minimal set first. Expand only for a named cross-layer question; do not bulk-read evidence, repomix XML, generated media, `.next`, `node_modules`, or historical plans.

| Project | Minimal context | Expanded context | Avoid by default |
| --- | --- | --- | --- |
| Source Proxy | `AGENTS.md`; worktree manifest; `source_proxy/context/canonical_broker.py`; `source_proxy/context/source_readiness.py`; `source_proxy/decision/prompt_packet.py`; matching `test_canonical_context_broker.py`, `test_context_source_readiness.py`, `test_prompt_packet_context_metadata.py` | `source_proxy/api/`, `source_proxy/decision/`, `src/app/coding/`, `src/components/coding/`, `src/lib/coding/`, `scripts/run-coding-e2e-loop.mjs` | SpiritFlix, media queues, `docs/evidence/`, repomixes, unrelated plans |
| SpiritFlix | `AGENTS.md`; manifest; route/component named by task; `scripts/spiritflix-prod-start.sh`; targeted test | `src/app/spiritflix/`, `src/components/spiritflix/`, `src/lib/`, Jellyfin/API boundary | Source Proxy internals, coding cockpit, generated media, bulk scans |
| Scout | manifest; `scout/`; the named manual-intake/receipt document | `source_proxy/decision/research.py`, documented Proxy boundary | providers, queues, and Source Proxy mutation paths |
| Cartographer | manifest; `source_proxy/cartographer/`; Level 13 boundary/gate | named contract tests and related plan only | runtime dispatch, branches, queues, implementation assumptions |
| Design | named `_blueprints/` artifact and named design packet | `data/design-vault/`, relevant frontend leaf | full visual evidence and unrelated cockpit code |
| Mac | manifest; Mac baseline doc; `scripts/mac-worker/`; `src/lib/mac-worker/` | Source Proxy worker adapter and focused tests | direct Windows-only path assumptions, remote writes |
| Shared/external | manifest; requested `src/`, `scripts/`, `config/`, or `apps/` path | only documented consumers | all product roots and archives |

Use symbol/call-site searches and bounded ranges. Record files read in the scope ledger; a second read needs a reason.
