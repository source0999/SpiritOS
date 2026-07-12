# SpiritOS Context Map

This is the authoritative routing map. Status is not a claim of integration: `partial`, `preview`, `test-only`, and `unknown pending architecture audit` must remain so until independently proven.

| Area | Purpose and status | Owner / host | Source roots and boundaries | Deep reference |
| --- | --- | --- | --- | --- |
| Shared SpiritOS | Next.js shell, shared scripts and docs; production/partial by subsystem | SpiritFlix worktree on Dell; SMB view `Z:\` | `src/`, `scripts/`, `config/`; shared edits need written justification | `docs/dev-setup/worktree-policy.md` |
| Source Proxy | Coding/proxy lifecycle and context broker; partial | `/home/source/SpiritOS-source-proxy-20260711` on Dell | `source_proxy/`, `/coding` roots; never mix with SpiritFlix | `source_proxy/context/` and test registry |
| SpiritFlix | Jellyfin/media experience; production/partial by route | `/home/source/SpiritOS` on Dell / `Z:\` | `src/app/spiritflix/`, `src/components/spiritflix/`, `scripts/spiritflix-*`; no Proxy service ownership | `scripts/spiritflix-prod-start.sh` |
| Scout/search | Research packets and manual intake; partial | Dell, Source Proxy boundary | `scout/`, `source_proxy/decision/research.py`; no unapproved promotion or provider mutation | `docs/scout-v0-5-scout-to-proxy-manual-import-design.md` |
| Cartographer | Mapping/observability contracts; preview/observe-only | Dell | `source_proxy/cartographer/`; no worker, Git, or write authority inferred | `docs/cartographer-level-13-closeout-and-level-14-gate.md` |
| Design agent/extractor | Design packets and blueprint artifacts; partial/planning-heavy | Dell | `_blueprints/`, `data/design-vault/`, design docs; do not treat packets as runtime consumption | `docs/design-agent-ecosystem-plan-16-closeout-v0.1.md` |
| Mac integration | Read-only support/search-worker lane; partial | Mac through Dell hop `spirit-mac-mini` | `scripts/mac-worker/`, `src/lib/mac-worker/`; no source write or hidden worker authority | `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md` |
| Model/provider adapters | Server-owned provider and worker configuration; partial | Dell Source Proxy | `source_proxy/decision/`, `source_proxy/agents/`; caller inputs are not authority | `source_proxy/tests/test_plan2_production_config_lock.py` |
| Subagent orchestration | Contracts, not dispatch authority; preview | Dell | `source_proxy/agent_factory/`, Cartographer docs | `docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md` |
| Coding cockpit | `/coding` frontend and proxy bridge; partial | Dell Source Proxy | `src/app/coding/`, `src/components/coding/`, `src/lib/coding/`, `source_proxy/api/` | `scripts/run-coding-e2e-loop.mjs` |
| Media/generated data | Library/queues and ingest output; runtime only | Dell / 8 TB storage | `media/`, `data/`, `tmp/`; do not load or commit by default | SpiritFlix scripts |
| Runtime/evidence/fixtures | Logs, databases, browser receipts and Prompt fixtures; non-authoritative unless named | Dell | `docs/evidence/`, `repomixes/`, `.next/`, caches; avoid by default | worktree policy |
| fold7-media-grabber | Media acquisition helper; unknown pending audit | Dell | `fold7-media-grabber/`; isolated from playback UI | its local README |
| Historical branches/bundles | Recovery/reference only | Dell | `/home/source/.spiritos-preservation/20260711-full-cleanup/`, inactive branches | manifest |

Allowed cross-project dependency is limited to an explicitly justified shared file, documented interface, or receipt. Presence of an import, plan, test, or package is not evidence of runtime execution or downstream consumption.
