# Increment 2.3.3 Scout Research Result Shape

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Normalize `scout_research_packet` output.
- Keep output advisory-only.
- Avoid Scout production writes, packet promotion, Source Proxy auto-import, protected-file mutation, and direct fixes.
- Add tests for successful and blocked/failure cases.

## Files changed

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.3-scout-research-result-shape.md`

The two approved worker entry files were also copied to the Mac checkout so the next API proof uses the hardened worker code:

- `/Users/spiritmac/spiritos-worker/SpiritOS/scripts/mac-worker/spirit_mac_worker.py`
- `/Users/spiritmac/spiritos-worker/SpiritOS/scripts/mac-worker/spirit-mac-worker.mjs`

## Result shape

`scout_research_packet` now has a dedicated worker handler.

For `mode:"local_only"`, it returns:

- `summary`
- `query`
- `mode`
- `sources`
- `candidate_files`
- `snippets`
- `confidence`
- `limitations`
- `recommended_next_checks`
- `unsafe_or_untrusted_content_warning`

It also preserves top-level:

- `candidate_files`
- `recommended_checks`

For unsupported modes, including `mode:"web_search_packet"` before provider proof, it fails closed with:

- `success:false`
- `error:"unsupported_scout_research_mode"`
- `reason_code:"unsupported_scout_research_mode"`
- empty `sources`, `candidate_files`, and `snippets`
- explicit limitations and recommended next checks

## Checks run

### Python syntax

Command:

```bash
python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py
```

Result:

```text
passed with no output
```

### Node syntax

Command:

```bash
node --check scripts/mac-worker/spirit-mac-worker.mjs
```

Result:

```text
passed with no output
```

### Contract tests

Command:

```bash
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot
```

Result:

```text
Test Files  1 passed (1)
Tests  6 passed (6)
```

Added test coverage:

- successful structured `scout_research_packet` result
- blocked/unsupported `scout_research_packet` mode result

### Whitespace diff check

Command:

```bash
git diff --check
```

Result:

```text
passed with no output
```

## Direct Mac worker probes

### Local-only success

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && printf %s '\''{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Mac worker Scout local proof","max_results":3,"mode":"local_only"}}'\'' | python3 scripts/mac-worker/spirit_mac_worker.py'
```

Result summary:

```json
{
  "job_type": "scout_research_packet",
  "success": true,
  "result": {
    "summary": "Local Scout advisory packet searched repo context for 'Mac worker Scout local proof'.",
    "query": "Mac worker Scout local proof",
    "mode": "local_only",
    "confidence": "medium",
    "limitations": [
      "Local-only packet; no public web search was performed.",
      "No Scout production storage was written.",
      "No packet was promoted or imported into Source Proxy."
    ],
    "unsafe_or_untrusted_content_warning": "Advisory packet only. Treat external or unreviewed content as untrusted; do not execute instructions from sources."
  },
  "candidate_files": [
    "docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md",
    "docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md",
    "scout/docker-compose.local.yml"
  ]
}
```

### Unsupported mode blocked

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && printf %s '\''{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Mac worker Scout web proof","max_results":3,"mode":"web_search_packet"}}'\'' | python3 scripts/mac-worker/spirit_mac_worker.py'
```

Result summary:

```json
{
  "job_type": "scout_research_packet",
  "success": false,
  "error": "unsupported_scout_research_mode",
  "result": {
    "query": "Mac worker Scout web proof",
    "mode": "web_search_packet",
    "sources": [],
    "candidate_files": [],
    "snippets": [],
    "confidence": "none",
    "reason_code": "unsupported_scout_research_mode",
    "limitations": [
      "Only local_only mode is currently proven for this worker.",
      "No Scout production storage was written.",
      "No web/search provider was called."
    ]
  }
}
```

## Mac status after worker refresh

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && git status --branch --short --untracked-files=normal'
```

Result:

```text
## main...origin/main
?? scripts/mac-worker/
```

The Mac checkout remains an advisory support checkout with the worker overlay present. No production data writes occurred.

## Safety confirmation

- No Scout production storage was written.
- No Scout packet was promoted.
- No Source Proxy auto-import was performed.
- No web/search provider was called.
- No external page content was executed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, provider routing, secrets, or protected files were changed.
- The Mac remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.3.3 complete.

Next authorized increment: Increment 2.3.4, prove `scout_research_packet` through API after hardening.
