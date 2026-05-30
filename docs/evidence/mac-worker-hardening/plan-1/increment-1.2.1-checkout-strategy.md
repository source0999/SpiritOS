# Increment 1.2.1 Checkout Strategy

Date: 2026-05-28

## Required commands run

```bash
cd /home/source/SpiritOS
git remote -v
ssh -o BatchMode=yes spirit-mac-mini 'git --version'
ssh -o BatchMode=yes spirit-mac-mini 'find /Users/spiritmac/spiritos-worker -maxdepth 2 -type d -name .git -print 2>/dev/null || true'
ssh -o BatchMode=yes spirit-mac-mini 'find /Users/spiritmac/spiritos-worker/SpiritOS -maxdepth 2 -type f | head -40 2>/dev/null || true'
```

## Evidence

### Linux remote

```text
origin	git@github.com:source0999/SpiritOS.git (fetch)
origin	git@github.com:source0999/SpiritOS.git (push)
```

### Mac Git availability

```text
git version 2.39.5 (Apple Git-154)
```

### Existing `.git` directories under Mac worker parent

```text
```

No `.git` directory was found under `/Users/spiritmac/spiritos-worker` at max depth 2.

### Existing Mac worker file sample

```text
/Users/spiritmac/spiritos-worker/SpiritOS/source_proxy/terminal_presets.py
/Users/spiritmac/spiritos-worker/SpiritOS/source_proxy/__init__.py
/Users/spiritmac/spiritos-worker/SpiritOS/source_proxy/self_status.py
/Users/spiritmac/spiritos-worker/SpiritOS/source_proxy/main.py
/Users/spiritmac/spiritos-worker/SpiritOS/scout/pytest.ini
/Users/spiritmac/spiritos-worker/SpiritOS/scout/requirements.txt
/Users/spiritmac/spiritos-worker/SpiritOS/scout/docker-compose.local.yml
/Users/spiritmac/spiritos-worker/SpiritOS/scout/SCOPE.md
/Users/spiritmac/spiritos-worker/SpiritOS/scout/Dockerfile
/Users/spiritmac/spiritos-worker/SpiritOS/scout/docker-compose.scout.yml
/Users/spiritmac/spiritos-worker/SpiritOS/scout/.gitignore
/Users/spiritmac/spiritos-worker/SpiritOS/scout/.env
/Users/spiritmac/spiritos-worker/SpiritOS/scout/THREAT_MODEL.md
/Users/spiritmac/spiritos-worker/SpiritOS/scout/.env.example
/Users/spiritmac/spiritos-worker/SpiritOS/package.json
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/gen-dev-cert.sh
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/validate-blueprints.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-bwrap-network-probe.sh
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-bwrap-probe.sh
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/next-mcp-ws-probe.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-context-compress.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-proxy-bootstrap.sh
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-proxy-bootstrap.ps1
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-proxy-dev.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/source-proxy-bootstrap.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/next-mcp-ws-smoke.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/next-mcp-ws-bridge.mjs
/Users/spiritmac/spiritos-worker/SpiritOS/tsconfig.json
/Users/spiritmac/spiritos-worker/SpiritOS/next.config.ts
/Users/spiritmac/spiritos-worker/SpiritOS/src/proxy.ts.bak
```

## Checkout strategy

Chosen strategy: preserve the existing targeted synced tree as a timestamped whole-directory backup, then clone a fresh real git checkout to the required final path.

Reasoning:

- The final path must remain `/Users/spiritmac/spiritos-worker/SpiritOS`.
- The current final path exists but is not a git checkout.
- The Mac has Git installed.
- Linux remote is `git@github.com:source0999/SpiritOS.git`.
- A fresh clone avoids pretending the targeted synced copy is a repository.
- The old tree contains `scout/.env`; its contents were not read. The backup operation must preserve the old tree as a whole and must not inspect, copy into the new checkout, or hardcode secret contents.

Planned Increment 1.2.2 steps:

1. Rename `/Users/spiritmac/spiritos-worker/SpiritOS` to a timestamped backup path.
2. Clone `git@github.com:source0999/SpiritOS.git` into `/Users/spiritmac/spiritos-worker/SpiritOS`.
3. Checkout Linux branch `main`.
4. Validate git status, HEAD, and worker script presence.

## Result

Increment 1.2.1 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized increment: Increment 1.2.2, create or repair Mac git checkout.
