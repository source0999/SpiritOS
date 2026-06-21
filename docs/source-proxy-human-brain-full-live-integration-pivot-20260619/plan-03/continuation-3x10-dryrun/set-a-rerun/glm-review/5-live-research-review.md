# Stage 5 — Live Research Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

Research prompts in scope: A1, A2, A3, A4, A5, A6, A9. (A7/A8/A10 are non-internet and correctly show `source_count=0`.)

**Raw provider evidence (`A*.research.raw.json`, `A*.model.attempt*.raw.json`, `A*.grader.attempt*.raw.json`) is NOT reachable on this seat** (Stage 0). So "provider returned live results" is judged indirectly: from the source lists embedded in each `A*.md` "Actual Research/Search Evidence" section (which the runner writes from `research.research_packet.sources`), from the runner code, and from the readiness probe in `2-real-harness-readiness.md` (which shows the SearXNG probe returned 13 results with real PKHeX titles). The readiness probe + real, specific source titles strongly suggest a live SearXNG provider was actually hit. The remaining question is whether the *final output depends on* those findings — judged from the work-product text.

## Per-prompt

### A1 — Pokémon save editor
- Source list real & specific: PKHeX (Project Pokémon), PKHeX for Web, Reddit save-editing guide, batch-editor tutorial, iOS guide. (`source_count=6`)
- `research_marker_hits`: `["reddit.com","pkhex-web.github.io"]`.
- Final output cites PKHeX as the framework and references batch editing / cross-platform web version — these are real findings, not generic slop. The plan is shaped by them (web version prioritized for accessibility).
- Minor: model mangled some URLs (`projectpo kemon.org` with a space) — cosmetic echo error, not fabrication.
- **Verdict: RESEARCH_ACCEPTED.** Live, specific, and the recommendation genuinely follows from the findings.

### A2 — Browser extension → Source Proxy task
- Source list real: Chrome Native messaging (developer.chrome.com), MDN Native messaging, Stack Overflow, MS Edge native messaging, text/plain.
- `research_marker_hits`: `["stackoverflow.com","learn.microsoft.com","textslashplain.com"]`.
- **Problem:** the work product's `Finding:`/`Source:` bullets echo **hallucinated domains** — `dexevelopeer.chrome.com` and `dexevelopeer.mozilla.org` (note the corruption `developer`→`dexevelopeer`). The correct sources appear in the separate "Actual Research/Search Evidence" section. So the model corrupted the domain strings it echoed, yet the grader still counted `stackoverflow.com`/`learn.microsoft.com`/`textslashplain.com` as hits (those happened to survive uncorrupted).
- The recommendation (Native Messaging + native host) is correct and is the right current approach, and it does cite MV3-era reality implicitly. But the materiality section is partly source-name echoing with corrupted hosts, and the grader passed on the surviving host fragments.
- **Verdict: RESEARCH_WEAK_BUT_ACCEPTABLE.** Research is real and the direction is right, but materiality evidence is corrupted-domain echo that the keyword grader could not catch.

### A3 — Android app to start proxy tasks + check receipts
- Sources real: Android sharing docs (developer.android.com), Kotlin Multiplatform samples, Jetpack Compose user-interaction, Medium share-button article, YouTube, Android messaging guide.
- Output ties research to the repo: names `long_running_tasks.py`, `route.ts`, `long_running_task_create` endpoint, Retrofit. Recommendation (ACTION_SEND intent + REST) is sound and research-shaped.
- Minor URL typo: `daveveloper.android.com` (corruption). Cosmetic.
- **Verdict: RESEARCH_ACCEPTED.** Genuine, repo-aware, research-shaped.

### A4 — Obsidian/project notes → better AI context
- Sources real: `brianpetro/obsidian-smart-connections` GitHub, r/ObsidianMD, smartconnections.app, Smart Plugins site, blog, community plugin page.
- Output recommends Smart Connections first, correctly links to repo files (`obsidian.py`, `obsidian_context.py`, env flags `OBSIDIAN_CONTEXT_ENABLED`/`OBSIDIAN_VAULT_PATH`), and gives a concrete 4-step build plan. Research visibly shapes the "build first" answer.
- Minor: a couple of env-var typos (`OBSIDIAN_INCUDE_GLOBS`, `OBSIDIAN_EXCCLUDE_GLOBS`) — model spelling errors, not fabrications.
- **Verdict: RESEARCH_ACCEPTED.** Strong; research clearly drives the recommendation.

### A5 — Local AI workstation (Dell/Mac/Windows), no wasted money
- Sources real: OpenClaw homelab, Ollama-vs-LM-Studio-2026 (kunalganglani), Docker+AMD homelab, YouTube private-AI-server, lmstudio.ai, Reddit r/ollama.
- `research_marker_hits`: `["kunalganglani.com","local llm with ollama","youtube.com","has anyone actually gotten","reddit.com"]` — **two of these are title fragments** (`local llm with ollama`, `has anyone actually gotten`), confirming the keyword/echo nature of the gate (Stage 2 weakness reproduced: a title-fragment echo scores a hit).
- **Materiality is shallow:** the three "How it changed the plan" bullets are generic restatements ("Prioritizes LM Studio as the primary UI…", "Incorporates Ollama as the backend…", "Confirms the viability…"). The recommendation ("LM Studio + Ollama on your Dell Mac") is not actually *changed* by the findings — it is the default popular answer the findings merely decorate.
- **Three-machine collapse:** the user asked about **Dell, Mac, and Windows** roles without wasting money. The plan treats "Dell Mac" as one machine, never assigns distinct roles to Dell vs Windows, and gives no cost/GPU guidance per box. The research (homelab GPU, Docker+AMD) that *should* have shaped a Dell-vs-Mac-vs-Windows split is not used to make that decision.
- **Mac proof:** see Stage 6 — `python3 --version` capability readback, not workstation validation.
- **Verdict: RESEARCH_NEEDS_FIX.** Live sources exist, but the output does not honestly use them for the actual ask (three-machine roles + cost), and materiality is decorative echo.

### A6 — Local media metadata cleanup, no Jellyfin/media mutation
- Sources real: r/jellyfin "what media management software", tinyMediaManager, r/jellyfin "fast way to clean up file names", Chocolatey HN, self-hosting guide, Homebrew Cask.
- Output recommends TinyMediaManager, correctly reasons that the no-mutation constraint rules out direct SpiritFlix integration, and names the right repo files. Research genuinely shapes the recommendation and the boundary is honored.
- **Verdict: RESEARCH_ACCEPTED.** Genuinely strong and honest; the best research-shaped record alongside A4.

### A9 — Current local LLM tools, "this month"
- Sources real: SitePoint 2026 guide, r/LocalLLaMA "best local LLMs as of March 2026", glukhov.org comparison, Pinggy top-5, YouTube, bizon-tech inference engines.
- **Output quality problem:** the work product contains **corrupted/garbled URLs and tokens** — literal `local_l لمs` (Arabic-character corruption of "llms"), `l لم-inference`, and a fabricated `vlvm` host in the glukhov comparison title echo. These are model-generation artifacts that the keyword grader ignored.
- `research_marker_hits`: `["reddit.com","glukhov.org","pinggy.io","youtube.com","bizon-tech.com"]` — pure domain echo.
- "This month/current" support: the cited Reddit thread is explicitly dated "March 2026" and several sources are 2026-dated, so currency is *partially* supported — but the work product does not state a month and does not explicitly limit freshness; it just says "for the current month."
- Recommendation (vLLM or LM Studio) is plausible and matches sources, but the comparison is thin and corrupted.
- **Verdict: RESEARCH_WEAK_BUT_ACCEPTABLE.** Live and roughly on-topic, with real 2026 currency signals, but the work product has garbled/corrupted content that a real usefulness grader would have rejected and the materiality is domain echo.

## Cross-cutting finding

For every research prompt, `research_materially_changed_output=true` was satisfied by the model emitting the prompt-mandated `Finding:/Source:/How it changed the plan:` template plus ≥2 source-domain/title echoes. In A2 (corrupted domains), A5 (title-fragment hits + three-machine collapse), and A9 (garbled tokens), the gate passed content that a usefulness grader should have flagged. This confirms Stage 2: the research lane is live, but the materiality grading is echo-driven, so a research PASS is not proof of research-shaped work.

## Summary table

| ID | Verdict |
|----|---------|
| A1 | RESEARCH_ACCEPTED |
| A2 | RESEARCH_WEAK_BUT_ACCEPTABLE |
| A3 | RESEARCH_ACCEPTED |
| A4 | RESEARCH_ACCEPTED |
| A5 | RESEARCH_NEEDS_FIX |
| A6 | RESEARCH_ACCEPTED |
| A9 | RESEARCH_WEAK_BUT_ACCEPTABLE |

## Overall

**live_research: PARTIAL.** The provider lane is genuinely live (real, specific, mostly 2026-dated sources across all 7 research prompts; readiness probe confirms SearXNG). But materiality grading is echo-driven, so the PASS does not certify that findings changed the recommendation — and A5 fails the actual user goal (three-machine cost-aware roles) while still passing the gate.
