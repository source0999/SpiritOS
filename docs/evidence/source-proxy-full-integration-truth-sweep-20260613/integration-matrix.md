# Integration Matrix

Status meanings: LIVE means invoked with evidence. WIRED_UNUSED means callable/routed conditionally but not seen in recent Level 3/4 artifact runs. PREVIEW_ONLY means explicit no-call/no-authority metadata. DOCS_ONLY means planning or docs only. DORMANT means code exists but no live prompt-path invocation found. MISSING means no implementation found.

| Subsystem | Intended role | Code exists | Docs/evidence exists | Runtime entrypoint exists | Invoked in recent Level 3/4 | Live transcript/log evidence | Status | Blockers | Next integration step | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen coder lane | primary local coder/action lane | YES | YES | YES | YES | YES | LIVE | narrow artifact focus | add per-prompt integration receipt | P0 |
| Hermes model lane | verifier/critic sidecar | YES | YES | preview only | NO | NO | PREVIEW_ONLY | no live call approval or transcript path | advisory verifier pilot with no PASS authority | P2 |
| Gemma model lane | context/spec/verifier sidecar | YES | YES | preview only | NO | NO | PREVIEW_ONLY | no live routing or privacy proof | context/spec packet pilot | P2 |
| verifier lane | advisory final/retest critic | YES | YES | packet builder only | NO as model lane | NO | PREVIEW_ONLY | `model_calls_enabled: false` | deterministic receipt first, then optional Hermes/Gemma advisory | P1 |
| Cartographer routing | future route/context owner | YES | YES | preview endpoint/code | NO | NO | PREVIEW_ONLY | live routing disabled by contract | add Cartographer decision receipt, still Source Proxy gated | P2 |
| Cartographer context | repo map/ownership context | YES | YES | many APIs | NO | NO | DORMANT | not injected into prompt packet | read-only context selector | P2 |
| Obsidian context | read-only notes context | YES | tests/API | YES manual query | NO | NO | WIRED_UNUSED | diagnostics only in coder path; not selected into prompt | context-needed router and receipt fields | P1 |
| Scout/search | local intelligence/search context | YES | YES | gated env/API | NO | NO | WIRED_UNUSED | disabled unless env; not artifact-routed | search-needed decision + Scout receipt | P1 |
| SearXNG | local web search provider | YES config | YES | conditional env URL | NO | NO | WIRED_UNUSED | not proven running in current session; no prompt call | local health + search receipt | P1 |
| xersearch/xersearchd | named local search | NO | NO | NO | NO | NO | MISSING | no repo matches found | decide whether real system or retire name | P3 |
| Mac worker | support-node advisory worker | YES scripts | YES | script/job runner | NO | NO | DORMANT | not called by Source Proxy prompt path | explicit advisory worker request/receipt | P3 |
| browser fetch/web research | direct web fetch/search | YES outside artifact path | README/config | conditional | NO | NO | WIRED_UNUSED | disabled/default-off; not artifact-routed | search-needed router and provider proof | P1 |
| Continue lane | external coder lane | evidence/docs | YES | not Source Proxy prompt route | NO | NO for Level 3/4 | DORMANT | no live routing from prompt-packet | keep separate until receipt model exists | P3 |
| Cursor lane | external coder lane | references only | sparse | NO | NO | NO | DOCS_ONLY | no current prompt-path integration found | inventory before integration | P3 |
| repair loop | bounded artifact repair | YES | YES | YES | YES | YES | LIVE | still artifact-only | receipt which model/context repair used | P0 |
| route traces | sidecar route proof | YES/evidence | YES | YES | YES | YES | LIVE | trace does not imply Cartographer ownership | add subsystem-used booleans | P0 |
| mini context pack | uploadable evidence summary | YES/evidence | YES | YES | YES | YES | LIVE | depends on accurate source receipts | include integration matrix summary | P0 |
| anti-tailoring audit | exact prompt-tailoring check | evidence scripts | YES | evidence-only | YES | YES | LIVE | scoped searches can miss broad code if timeout | standardize scope and record commands | P0 |
| anti-cheat audit | false PASS / fallback check | evidence scripts | YES | evidence-only | YES | YES | LIVE | artifact evidence only | standardize non-Qwen subsystem checks | P0 |
