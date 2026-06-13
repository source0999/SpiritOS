# Terminal Verification

Commands run during this sweep:

```powershell
Get-Content -LiteralPath 'C:\Users\smith\.codex\attachments\24e05aa8-b799-48c8-82bf-a75c3f36cf9f\pasted-text.txt'
Select-String -Path 'C:\Users\smith\.codex\memories\MEMORY.md' -Pattern 'Source Proxy|Level 3|Level 4|Cartographer|xersearch|Obsidian|Gemma|Hermes' -Context 1,2
Get-Location
git status --branch --short --untracked-files=normal
rg --files -g '!*node_modules*'
Get-ChildItem -LiteralPath 'docs\evidence' -Force
rg --files source_proxy
rg --files -g '*source*proxy*' -g '!node_modules' -g '!*.png' -g '!*.jpg'
rg -n 'Cartographer|cartographer|Obsidian|obsidian|SearXNG|searx|xersearch|Scout|scout|Gemma|gemma|Hermes|hermes|Mac worker|mac worker|verifier|route trace|mini context|context packet|SOURCE_PROXY' -g '!node_modules'
Get-ChildItem -LiteralPath 'docs\evidence\source-proxy-level-3-semantic-generalization-gate-b-20260613' -Recurse -File
Get-ChildItem -LiteralPath 'docs\evidence\source-proxy-level-4-first-hard-artifact-proof-20260613' -Recurse -File
Get-Content -LiteralPath 'source_proxy\api\decision.py'
Get-Content -LiteralPath 'source_proxy\tasks\long_running.py'
Get-Content -LiteralPath 'source_proxy\decision\model_lanes.py'
Get-Content -LiteralPath 'source_proxy\decision\verifier_lane.py'
Get-Content -LiteralPath 'source_proxy\decision\cartographer_routing.py'
Get-Content -LiteralPath 'source_proxy\context\obsidian.py'
Get-Content -LiteralPath 'source_proxy\api\obsidian_context.py'
Get-Content -LiteralPath 'source_proxy\decision\research.py'
Get-Content -LiteralPath 'source_proxy\decision\scout_research.py'
Get-Content -LiteralPath 'source_proxy\api\scout_intake.py'
Get-Content -LiteralPath 'source_proxy\proxy_memory\scout_intake.py'
Get-Content -LiteralPath 'backend\docker-compose.yml'
Get-Content -LiteralPath 'backend\searxng.yml'
rg -n 'xersearch|xersearchd' -g '!node_modules'
docker ps --filter name=searxng --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
Get-ChildItem Env: | Where-Object { $_.Name -match 'SEARX|WEB_SEARCH|SCOUT|OBSIDIAN|SOURCE_PROXY_CODER|SOURCE_PROXY_SCOUT|SOURCE_PROXY_PROJECT|SPIRIT_PROJECT|OLLAMA' }
Get-Content -LiteralPath 'scripts\mac-worker\spirit_mac_worker.py'
Get-Content -LiteralPath 'scripts\mac-worker\spirit-mac-worker.mjs'
Get-Content -LiteralPath 'docs\mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md'
Get-Content -LiteralPath 'docs\mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md'
Get-Content -LiteralPath 'source_proxy\cartographer\lane_registry.py'
Get-Content -LiteralPath 'source_proxy\api\cartographer.py'
Get-Content -LiteralPath 'source_proxy\main.py'
```

Preflight status observed:

```text
## master
?? docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/
```

Validation commands required for closeout:

```powershell
python -m json.tool docs/evidence/source-proxy-full-integration-truth-sweep-20260613/mini-context-pack.json
python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-full-integration-truth-sweep-20260613/mini-context-pack.xml')"
git diff --check -- docs/evidence/source-proxy-full-integration-truth-sweep-20260613
git status --branch --short --untracked-files=normal
```
