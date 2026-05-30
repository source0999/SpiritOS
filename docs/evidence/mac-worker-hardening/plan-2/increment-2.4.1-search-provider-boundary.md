# Increment 2.4.1 Search Provider Boundary

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Identify how SpiritOS/Scout currently does search.
- Identify whether SearXNG, local Scout search provider, or another search route is available.
- Identify whether Mac should call internet directly or ask Linux/Scout provider.
- Preserve local-first and cost-controlled boundaries.
- Do not add a paid provider.
- Do not create uncontrolled internet scraping.

No implementation files were changed.

## Required/possible command results

### Search/provider references

Command:

```bash
grep -R "searxng\|search_provider\|discovery" -n scout source_proxy src scripts docs 2>/dev/null | head -80 || true
```

Result summary:

- Scout has controlled search provider docs under `scout/docs/V0_3_PHASE2_CONTROLLED_SEARCH_PROVIDER.md`.
- Scout search provider implementation exists in `scout/src/scout/sources/search.py`.
- Scout discovery job API has `search-preview` and `extract-candidates` paths.
- Docs state `search-preview` has `candidate_effect:"none"`.
- Docs state candidate extraction may create/update Scout candidate records and should remain manual/bounded.
- `SCOUT_SEARXNG_URL` appears in Scout docs and config examples.

### Linux SearXNG HTML probe

Command:

```bash
curl -fsS http://127.0.0.1:8080/search?q=mac+worker 2>/dev/null | head || true
```

Result summary:

```text
<!DOCTYPE html>
<html class="no-js theme-auto center-alignment-no" lang="en-EN" >
...
<meta name="generator" content="searxng/2026.5.10+df1f24fb7">
```

Interpretation: SearXNG is available on the Linux host at `127.0.0.1:8080`.

### Mac TCP reachability

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'python3 - <<PY
import socket
for host, port in [("127.0.0.1",8080),("source-server.local",8080),("10.0.0.1",8080)]:
    s=socket.socket()
    s.settimeout(2)
    try:
        s.connect((host, port))
        print(f"OK {host}:{port}")
    except Exception as e:
        print(f"NO {host}:{port} {e}")
    finally:
        s.close()
PY'
```

Result:

```text
NO 127.0.0.1:8080 [Errno 61] Connection refused
OK source-server.local:8080
NO 10.0.0.1:8080 timed out
```

Interpretation: the Mac cannot use its own loopback for Linux SearXNG, but can reach the Linux host provider at `source-server.local:8080`.

### JSON probes

Linux command:

```bash
curl -fsS 'http://127.0.0.1:8080/search?q=mac+worker&format=json' 2>/dev/null | head -c 1200 || true
```

Linux result summary:

```json
{
  "query": "mac worker",
  "number_of_results": 0,
  "results": [],
  "unresponsive_engines": [
    ["brave", "too many requests"],
    ["duckduckgo", "timeout"],
    ["google", "timeout"],
    ["karmasearch", "access denied"],
    ["startpage", "timeout"]
  ]
}
```

Mac command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'python3 - <<PY
from urllib.request import Request, urlopen
url="http://source-server.local:8080/search?q=mac+worker&format=json"
try:
    req=Request(url, headers={"User-Agent":"SpiritOS-MacWorker-Proof/1"})
    with urlopen(req, timeout=5) as r:
        body=r.read(1000)
        print(r.status, r.headers.get("content-type"))
        print(body.decode("utf-8", "replace")[:1000])
except Exception as e:
    print(type(e).__name__, e)
PY'
```

Mac result summary:

```text
200 application/json
{"query": "mac worker", "number_of_results": 0, "results": [{"url": "https://admh.academy.reliaslearning.com/...
```

Interpretation: the Mac can receive JSON search responses from the local SearXNG provider via `source-server.local:8080`.

## Evidence answers

### Is a local search provider available?

Yes. SearXNG is reachable on Linux at `http://127.0.0.1:8080`.

### Is SearXNG available?

Yes. The HTML probe identifies SearXNG `2026.5.10+df1f24fb7`, and JSON probes return SearXNG JSON payloads.

### Can Mac reach it?

Yes, through `http://source-server.local:8080`. The Mac cannot reach Linux SearXNG through Mac loopback `127.0.0.1:8080`.

### Is the Mac supposed to browse directly or only request packets?

For A+ advisory support, the Mac should not do uncontrolled direct browsing. It should request bounded packets from a local-first provider boundary.

The safest current path is for `scout_research_packet` `mode:"web_search_packet"` to call the local SearXNG JSON endpoint with strict timeout and max-result bounds, return source URLs/titles/snippets, mark content as untrusted, and avoid Scout production storage.

### Safest A+ proof path

Implement a fail-closed `web_search_packet` mode in `scout_research_packet` that:

- defaults to local-first SearXNG candidates such as `source-server.local:8080` and `127.0.0.1:8080`
- avoids paid APIs
- uses short timeouts
- caps results
- returns structured source URLs/titles/snippets
- clearly labels untrusted content
- does not call Scout candidate extraction
- does not write Scout production storage
- does not execute page content
- returns structured `success:false` provider status when SearXNG is unavailable

## Safety confirmation

- No implementation files were changed.
- No Scout production storage was mutated.
- No Scout packet was promoted.
- No Source Proxy auto-import was performed.
- No paid provider was used.
- No uncontrolled internet scraping was added.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.4.1 complete.

Next authorized increment: Increment 2.4.2, implement or repair safe Mac search packet mode.
