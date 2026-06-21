# Stage 5 — Work Product Usefulness Review

Scoring the **content** of each work product on the 0-5 rubric, then noting the provenance caveat. Scores reflect "if a competent person had handed Britton this text, would it help him act?" They do NOT validate that the proxy produced it — by Stage 2/4 it did not.

Rubric: 5 immediately useful/specific/safe/actionable · 4 useful w/ minor gaps · 3 plausible but generic · 2 weak/template · 1 not useful · 0 missing.

| Prompt | Recommendation clear | Reasons | Source-backed (current) | Limitations | First slice / next action | Risks & boundaries | Handoff packet | Score | Notes |
|-------:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--|
| A1 | yes | yes | no proof | yes | yes (read-only inspector) | yes (no writes until checksums) | brief | 4 | Good route; handoff terse, no file/API surface for the save-editor itself |
| A2 | yes | yes | no proof | yes | yes (intake-only ext) | yes (forbidden captures) | good | 4 | Names real endpoints `/v1/tasks/long-running`; policy caps sensible |
| A3 | yes | yes | no proof | yes | yes (3 screens) | weak | brief | 4 | Solid native-vs-Capacitor call; light on auth/Tailscale specifics |
| A4 | yes | yes | no proof | yes | yes (sidecar index first) | yes (no Obsidian mutation) | brief | 4 | Clear "build the index, not the plugin" framing |
| A5 | yes | yes | no proof | yes (self-contradictory) | yes (stabilize receipts first) | yes (no hardware spend) | brief | 3 | Useful spend-nothing plan, but Mac evidence contradicts its own PASS; weakest on proof |
| A6 | yes | yes | no proof | yes | yes (inventory -> preview -> approve) | excellent (no DB/media/config) | good | 5 | Strongest: explicit forbidden surfaces, ranked tools, staged cleanup |
| A7 | yes | yes | n/a (no search) | yes | yes (receipt surface) | yes (preserve Plan 1-3 gates) | brief | 4 | Self-aware: identifies receipts as the anti-cheat lever |
| A8 | yes | yes | n/a | yes | yes (4 panels) | weak | brief | 4 | Concrete lane-matrix design over existing fields |
| A9 | partial | yes | no proof (currency) | yes | yes (keep Ollama) | yes (skip vLLM/SGLang) | brief | 3 | Reasonable but "this month" unsupported |
| A10 | yes | yes | n/a | yes | yes (receipt normalization task) | excellent (forbidden list) | good | 4 | Safe, scoped outside-AI packet; reuse of static repo context |

## Aggregate

- Average score: **3.9** (39/10).
- Lowest score: **3** (A5, A9).
- Weak prompts (under 4): A5, A9.
- No prompt below 3; none at 0.

## Usefulness checks

- Would this help Britton act? Yes for most (A1-A4, A6-A8, A10); weakly for A5/A9 on proof.
- Would another coding agent know what to do next? Mostly yes; A6 and A10 give the clearest "do/don't-touch" scope. A1's handoff is the vaguest (no concrete repo target since the editor is greenfield).
- Limitations stated? Yes on all ten (`limitations_stated=true`), and the text genuinely contains limitations.
- Protected paths / safety boundaries clear when relevant? Strongest on A6 (no DB/media/config/Docker) and A10 (no SpiritFlix/media/Jellyfin/Plan 4/route replacement).
- Model/API/CLI recommendations present when useful? Yes — A9 (Ollama vs LM Studio vs vLLM), A2 (MV3 + native messaging + MCP), A3 (Compose vs Capacitor).
- Plan specific enough to execute? A6, A8, A10 yes; A1/A5 lighter.

## Verdict

Work product usefulness: **PARTIAL**.
- Content quality is good (avg 3.9, no sub-3 scores), so the *text* clears a "useful enough" bar in isolation.
- But the acceptance rule requires average >= 4 **and** the content must come from a real run. The average sits just below 4, and two prompts (A5, A9) are weak on evidence/currency.
- Combined with the Stage 2/4 finding that these are pre-written strings, the usefulness scores describe a competent *draft*, not a validated daily-driver output.

Set A should not be accepted on usefulness alone: the bar (avg >= 4, none < 4, real provenance) is not met.
