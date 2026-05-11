Source Proxy Web Research Integration Plan – Phase 1
Goal: Make the Source Proxy the central decision gateway that can detect research-heavy prompts, safely call your local SearXNG (reusing the existing provider router), and return enriched route decisions / prompt packets that include real sources.
Core rule: The proxy stays 100% read-only. No filesystem writes, no direct LLM calls, no bypassing approval gates.
Scope of Phase 1 only:

Add research detection inside the existing decision router.
Add a lightweight, optional local web search step (using the existing src/lib/server/web-search/ machinery via a new internal helper).
Extend the prompt-packet and route-decision payloads to optionally include verified sources.
All changes are behind feature flags and manual tests.

Do not proceed to Phase 2 (frontend wiring) until this phase is fully verified.

Increment 1.1: Add research detection to the decision router (purely internal)
Files to change:

source_proxy/decision/router.py – add a new helper needs_research
source_proxy/decision/__init__.py (if needed for exports)

What to do (exact steps for Codex):

In router.py, after the existing decide_route logic, add a private function:Pythondef needs_research(task: str, context_tokens: int | None = None) -> bool:
    # simple keyword + intent based detection
    ...
Update DecisionInput and RouteDecision to include a research_recommended: bool flag (default False).
In decide_route, set research_recommended = needs_research(...) when task looks like current events, verification, "latest", "current", "news", "what's new", etc.

Manual check after this increment:
Bashcurl -k -X POST https://localhost:8787/v1/decisions/route \
  -H "Content-Type: application/json" \
  -d '{"task":"What are the latest changes in Vite 6?","needs_codebase_context":false}'
Expected outcome:

Response contains "research_recommended": true (and the usual recommended_route, reason_codes).

Debugging steps:

print the task_classification and research_recommended temporarily.
Run python -m pytest source_proxy/tests/test_source_proxy_end_to_end.py -q --tb=no to ensure existing tests still pass.

Next step: Tell me “Increment 1.1 done” → I will give you Increment 1.2.

Increment 1.2: Create a safe research preview helper that calls local SearXNG
Files to change:

New file: source_proxy/decision/research.py (create it)
Update source_proxy/decision/router.py to import and use it

What to do:

In the new research.py, add one function:Pythonasync def run_local_research_preview(query: str, max_results: int = 6) -> list[dict]
It must reuse the existing web search provider router (src/lib/server/web-search/provider-router.py is already imported elsewhere — call it the same way the main Spirit backend does).
Only use searxng provider (respect SEARXNG_URL).
Return clean list of {title, url, snippet} only — never raw HTML or full pages.


Manual check:
Run the new helper directly in Python REPL or add a temporary test endpoint and curl it.
Expected outcome:

Returns real sources from your local SearXNG (not empty, not fake).

Debugging steps:

Check SEARXNG_URL=http://127.0.0.1:8080 is set.
Verify SearXNG container is running (docker compose --profile local-search ps).
Look for any provider=searxng logs.

Next step: Tell me “Increment 1.2 done”.

Increment 1.3: Wire research preview into prompt-packet and route decision
Files to change:

source_proxy/decision/prompt_packet.py
source_proxy/decision/router.py
source_proxy/api/decision.py (update the Pydantic models slightly)

What to do:

When research_recommended is true, call the new run_local_research_preview and attach the sources to the payload.
Add optional field research_sources: list[dict] to the prompt-packet response.

Manual check:
Same curl as 1.1 but now expect research_sources array with real titles/URLs from SearXNG.
Expected outcome:

Prompt packet contains actual fresh sources (e.g. Vite release notes) instead of “I don’t have current info”.

Debugging steps:

Check response time (should still be fast — SearXNG is local).
Verify sources are filtered to only verified http(s) URLs.

Next step: Tell me “Increment 1.3 done”.

Increment 1.4: Add feature flag + comprehensive end-to-end test
Files to change:

source_proxy/decision/router.py (add SPIRIT_ENABLE_PROXY_RESEARCH env flag, default false)
source_proxy/tests/test_source_proxy_end_to_end.py (add one new test case)

Manual check:

Set SPIRIT_ENABLE_PROXY_RESEARCH=true in .env.local
Restart proxy
Run the full test suite: python -m unittest discover source_proxy/tests

Expected outcome:

45 tests passing (one new test that exercises the research path).

Debugging steps:

If test fails, run with -v for details.
Check proxy logs for “research preview used”.

Next step: Tell me “Increment 1.4 done — all tests green”.

Increment 1.5: Update tools manifest + action preview to document the new capability
Files to change:

source_proxy/self_status.py (update build_tools_manifest)
source_proxy/api/action_preview.py (optional safety message for research actions)

Manual check:
Bashcurl -k https://localhost:8787/v1/tools/manifest
Expected outcome:

Tools manifest now lists a new research_preview capability under enabled tools.

Final verification for Phase 1:
Run your earlier test prompts again (latest Vite, Fetch API teaching, etc.) and confirm the proxy now returns sources.

Once you complete all 1.x increments and confirm “Phase 1 complete – all manual checks passed”, reply with that exact phrase.
I will then give you Phase 2 (safe frontend wiring) with the same level of explicit, Codex-ready increments.
This plan is deliberately tiny, testable at every step, and contains zero hallucination risk. Start with Increment 1.1 whenever you’re ready.