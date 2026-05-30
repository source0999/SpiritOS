# Increment 2.2.2 Worker Overlay Formalized

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Formalize `scripts/mac-worker/` safely.
- Bring required non-secret worker files into tracked repo content.
- Add documentation explaining the Mac worker checkout/operator contract.
- Do not copy secrets, private keys, `.env.local`, cache files, or generated local state.

## Files changed

Staged as tracked repo content:

- `scripts/mac-worker/spirit-mac-worker.mjs`
- `scripts/mac-worker/spirit_mac_worker.py`
- `docs/mac-worker-operator-contract.md`

Evidence file created:

- `docs/evidence/mac-worker-hardening/plan-2/increment-2.2.2-worker-overlay-formalized.md`

Excluded:

- `scripts/mac-worker/__pycache__/`

`__pycache__/` is already ignored by `.gitignore`.

## Secret/cache review

Command:

```bash
git check-ignore -v scripts/mac-worker/__pycache__ scripts/mac-worker/__pycache__/* || true
```

Result:

```text
.gitignore:8:__pycache__/	scripts/mac-worker/__pycache__
.gitignore:8:__pycache__/	scripts/mac-worker/__pycache__/spirit_mac_worker.cpython-312.pyc
```

Command:

```bash
grep -RInE "SECRET|TOKEN|KEY|PASSWORD|PRIVATE|BEGIN|env\.local|api[_-]?key" scripts/mac-worker || true
```

Result:

```text
```

No matching secret-like strings were found in `scripts/mac-worker/`.

Note: `rg` was attempted first but was unavailable in this shell, so `grep` was used as fallback.

## Required checks

### Git status

Command:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Result summary:

```text
## main...origin/main
A  docs/mac-worker-operator-contract.md
A  scripts/mac-worker/spirit-mac-worker.mjs
A  scripts/mac-worker/spirit_mac_worker.py
```

The full status still includes pre-existing unrelated modified and untracked files from before this increment. The important formalization result is that the two worker files now show as staged additions instead of untracked `?? scripts/mac-worker/`.

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

### Whitespace diff check

Command:

```bash
git diff --check
```

Result:

```text
passed with no output
```

## Mac worker execution check

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && printf %s '\''{"job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"}}'\'' | python3 scripts/mac-worker/spirit_mac_worker.py'
```

Result summary:

```json
{
  "job_type": "system_status",
  "success": true,
  "result": {
    "summary": "Mac worker status returned",
    "hostname": "spirit-mac-mini.local",
    "platform": "darwin",
    "arch": "x86_64",
    "repo_path": "/Users/spiritmac/spiritos-worker/SpiritOS",
    "repo_present": true,
    "supported_job_types": [
      "repo_context_search",
      "source_proxy_context_discovery",
      "trial_context_assist",
      "scout_research_packet",
      "browser_design_check",
      "run_safe_check",
      "system_status"
    ]
  }
}
```

## Operator contract

Created `docs/mac-worker-operator-contract.md`.

The contract states:

- Mac worker is advisory/check support only.
- Source Proxy remains approval and write authority.
- Expected Mac checkout path is `/Users/spiritmac/spiritos-worker/SpiritOS`.
- Worker entry files live in tracked `scripts/mac-worker/`.
- Local caches, secrets, `.env.local`, private keys, logs, screenshots, and machine-specific state must not be tracked.
- Mac must not apply fixes, mutate Cartographer or Scout production data, change provider routing, start hidden workers, install daemons/launch agents, or gain autonomous write authority.

## Safety confirmation

- No secrets were added.
- No `.env.local` file was added.
- No local cache file was added.
- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Scout production data, Cartographer data, provider routing, secrets, or protected files were mutated.
- The Mac worker remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.2.2 complete.

Next authorized increment: Phase 2.2 closeout.
