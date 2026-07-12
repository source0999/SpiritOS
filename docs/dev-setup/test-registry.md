# Test and Harness Registry

Run from the selected checkout. Commands marked `NOT_PROVEN` are deliberately not substitutes for runtime proof. Generated fixture/evidence output is state-changing and must remain ignored unless a receipt is expressly named.

| Lane | Smoke / focused | Full / build | Browser/runtime | Host | State-changing | Proves / does not prove |
| --- | --- | --- | --- | --- | --- |
| Source Proxy canonical broker | `.venv-source-proxy/bin/pytest -q source_proxy/tests/test_canonical_context_broker.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_prompt_packet_context_metadata.py` | focused context matrix only; broad regression is `npm run test:coding-regression` (verify venv) | `npm run context:verify`; not browser proof | Dell SSH | no / some fixtures | broker/readiness metadata; not downstream consumption |
| Source Proxy lifecycle/Undo/reset | `npm run test:coding-regression` | `npm run test:coding-frontend-regression`, then `npm run build` | `node scripts/run-coding-e2e-loop.mjs` only after service identity check | Dell SSH | harness fixtures may change | contracts/UI; e2e must report graded result, not merely render |
| Source Proxy health/CWD | `curl -kfsS https://127.0.0.1:8787/healthcheck` plus `/proc/<pid>/cwd` | n/a | ports 8787, 3000, expected 3002 | Dell SSH | no | running checkout identity; no product acceptance |
| Source Proxy managed v4 | NOT_PROVEN: locate a named current harness before running | NOT_PROVEN | do not substitute another e2e loop | Dell SSH | unknown | no claim until named harness and receipt are found |
| SpiritFlix client | targeted `vitest run <named test>` | `npm run typecheck`; `npm run build` | `npm run spiritflix:perf`, `npm run spiritflix:benchmark:mobile` after production start | Dell SSH (not SMB) | perf output yes | build/static behavior; browser/live playback needs browser evidence |
| SpiritFlix load/perf | `npm run spiritflix:perf:synthetic` | `node scripts/spiritflix-anime-performance-harness.mjs` when task fits | production URL only after CWD/port check | Dell SSH | yes | synthetic/perf metrics; not general playback correctness |
| Mac/design/Scout | named focused tests or receipt only | NOT_PROVEN globally | availability: `ssh spirit 'ssh -o BatchMode=yes spirit-mac-mini ...'` | Dell hop | no | host/path availability; not worker authority or integration |

Test sequencing: focused before build/broad matrix; run serially if the selected lane is I/O-bound; record cleanup/reset from the invoked harness itself rather than inventing one.
