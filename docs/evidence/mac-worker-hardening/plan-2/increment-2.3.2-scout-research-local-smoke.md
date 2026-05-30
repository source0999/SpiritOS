# Increment 2.3.2 Scout Research Local Smoke

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Run `scout_research_packet` through `/api/coding/mac-worker`.
- Use a local/repo-focused query.
- Capture exact failure honestly if the job fails.

No implementation files were changed.

## Required command

Command:

```bash
cd /home/source/SpiritOS

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Source Proxy Mac worker advisory search packet local repo proof","max_results":5,"mode":"local_only"}}'
```

Result:

```text
curl exited with code 7 and no response body.
```

## Interpretation

The local HTTPS app endpoint at `https://127.0.0.1:3000/api/coding/mac-worker` was not reachable during this increment.

This increment does not prove `scout_research_packet` through the SpiritOS API.

No success is claimed.

## Safety confirmation

- No implementation files were changed.
- No Scout production storage was mutated.
- No Scout promotion or intake endpoint was called.
- No external internet search was called.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.3.2 complete as an honest failed smoke.

NO-GO for marking `scout_research_packet` proven through API from this increment.

Next authorized increment: Increment 2.3.3, harden `scout_research_packet` result shape.
