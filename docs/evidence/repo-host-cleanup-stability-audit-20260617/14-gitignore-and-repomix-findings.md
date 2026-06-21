# Gitignore and Repomix Findings

## Inspected Files and Scripts

```
===== .gitignore
# ── Spirit OS - ignore build noise, secrets, and fat artifacts ─────────────────
.DS_Store
node_modules
.venv-source-proxy
.venv-source-proxy-windows
.venv/
.venv
.venv-*/
**/.venv/
__pycache__/
*.py[cod]
.next
.next.backup-*/
out
*.tsbuildinfo
.env.local
.claude/settings.local.json
npm-debug.log*
yarn-debug.log*
yarn-error.log*

oldSpiritOS.xml
models/
*.gguf
backend/.env
backend/**/*.log
data/source-proxy/*.json
.cursor/

certificates

# ── SpiritOS AI / temp / generated junk (post-cleanup) ─────────────────────
/attaches
/can
/concrete
/correct
/dev_commands
/does
/file
/hardware
/next
/Oracle
/POST
/probe
/routes
/see
/tool
/typo
/vague
SPIRIT_ENABLE_DEV_COMMAND_TOOLS=false
spirit_oracle_fairy_demo.*
spiritos_dashboard_finished_demo*
spirit-os@*

# Repomix outputs (never commit)
repomix-output*.xml
repomix-output*.ast*

# Heavy local media and archives. Keep source assets outside git unless a
# future commit explicitly uses Git LFS or another reviewed storage path.
*.mp4
*.mov
*.m4v
*.avi
*.mkv
*.webm
*.zip
*.7z
*.rar
*.tar
*.tar.gz
*.tgz

# Common temp
*.log
*.tmp
OIWWJQ~A
I8JTCW~Z
OV31EM~O
PNJICG~8
idian context must be read-only, optional, and disabled by default unless configured."
ource_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode*
proven model-authored output."
.DS_Store
Thumbs.db

# Local Playwright / Codex smoke screenshots (never commit)
.codex-smoke/
.codex-remote-attachments/
.codex-*.pid

# Local coder gate runtime state (README is tracked; state.json is operator-local)
.gate/state.json

# Rotated local env backups
.env.local.backup.*

# Fat local runner logs (Codex / probes / source-proxy); keep out of git + repomix
.codex-next-*.log
.codex-next-*.err.log
.probe-*.log
.source-proxy-*.log
.source-proxy-*.err.log

# Local Source Proxy runtime artifacts
source_proxy/.spirit-backups/
source_proxy/data/*.jsonl
source_proxy/data/*.sqlite3
source_proxy/**/__pycache__/
source_proxy/**/*.py[cod]

# Local root runtime artifacts
.spirit-backups/
data/coding-runs.json
data/*.jsonl
data/*.sqlite3

# Local Scout backup/data exports
scout/data.backup-*/

# Local Scout virtualenv and backups
scout/.venv/
scout/data.backup-*/

# Local generated/runtime artifacts
scout/.venv/
scout/data.backup-*/
tmp/
data/source-proxy/visual-index/
docs/evidence/**/workspace/
docs/evidence/**/http-server.pid

# Local face-organizer outputs and private review artifacts
scripts/media/backups/
scripts/media/review_exports/
scripts/media/known_performers/
scripts/media/face_verification_report.html
scripts/media/*manifest*.json
scripts/media/rename_plan.json
===== repomix.config.json
{
  "$schema": "https://repomix.com/schemas/latest/schema.json",
  "input": {
    "maxFileSize": 2000000
  },
  "output": {
    "filePath": "repomix-output.full.xml",
    "style": "xml",
    "parsableStyle": true,
    "compress": true,
    "fileSummary": true,
    "directoryStructure": true,
    "files": true,
    "truncateBase64": true,
    "topFilesLength": 10,
    "git": {
      "sortByChanges": true,
      "sortByChangesMaxCommits": 100,
      "includeDiffs": false,
      "includeLogs": false
    }
  },
  "include": ["**/*"],
  "ignore": {
    "useGitignore": true,
    "useDotIgnore": true,
    "useDefaultPatterns": true,
    "customPatterns": [
      "**/__tests__/**",
      "**/*.test.*",
      "**/*.spec.*",
      "repomix-output*",
      ".next",
      "dist",
      "node_modules",
      ".git",
      ".spirit-backups/**",
      "source_proxy/.spirit-backups/**",
      "source_proxy/data/**",
      "backend/searxng_data/**",
      "backend/volumes/**",
      "src/components/dashboard/demo-v4/**",
      "src/app/design-demo/**",
      "**/*demo*.*",
      "spirit_oracle_fairy_demo*",
      "spiritos_dashboard_finished_demo*",
      "_blueprints/**"
    ]
  },
  "security": {
    "enableSecurityCheck": true
  },
  "tokenCount": {
    "encoding": "o200k_base"
  }
}
===== package.json
{
  "name": "spirit-os",
  "version": "0.1.0",
  "private": true,
  "bin": {
    "repomix": "./scripts/repomix-llm.mjs"
  },
  "scripts": {
    "dev": "next dev -H 0.0.0.0 --webpack",
    "dev:https": "next dev -H 0.0.0.0 --webpack --experimental-https -p 3000",
    "dev:https:lan": "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https --experimental-https-key ./certificates/spirit-dev-key.pem --experimental-https-cert ./certificates/spirit-dev.pem",
    "dev:https:lan:watch": "bash ./scripts/spiritos-lan-watchdog.sh",
    "lan:restart": "bash ./scripts/restart-spiritos-lan.sh",
    "proxy:lan:restart": "bash ./scripts/restart-source-proxy-lan.sh",
    "spiritflix:stable:restart": "bash ./scripts/restart-spiritflix-stable-3001.sh",
    "lanes:audit": "bash ./scripts/runtime-lanes-audit.sh",
    "spiritflix:admin:dev": "bash ./scripts/spiritflix-admin-dev.sh start",
    "spiritflix:admin:dev:stop": "bash ./scripts/spiritflix-admin-dev.sh stop",
    "dev:turbo": "next dev -H 0.0.0.0",
    "dev:backend": "cd backend && docker compose up -d",
    "dev:all": "npm run dev:backend && npm run dev",
    "dev:all:https": "npm run dev:backend && npm run dev:https",
    "dev:all:https:lan": "npm run dev:backend && npm run dev:https:lan",
    "gate:status": "node ./scripts/gate-status",
    "gate:approve": "node ./scripts/gate-approve",
    "gate:start": "node ./scripts/gate-start",
    "gate:complete": "node ./scripts/gate-complete",
    "gate:block": "node ./scripts/gate-block",
    "proxy:bootstrap": "node ./scripts/source-proxy-bootstrap.mjs",
    "proxy:bootstrap:linux": "bash ./scripts/source-proxy-bootstrap.sh",
    "proxy:bootstrap:windows": "powershell -ExecutionPolicy Bypass -File ./scripts/source-proxy-bootstrap.ps1",
    "proxy:dev": "node ./scripts/source-proxy-dev.mjs",
    "proxy:https": "node ./scripts/source-proxy-dev.mjs --https",
    "proxy:https:lan": "node ./scripts/source-proxy-dev.mjs --https --lan",
    "context:pack": "node ./scripts/repomix-llm.mjs --config repomix.config.json .",
    "context:pack:full": "node ./scripts/repomix-llm.mjs --config repomix.config.json --full .",
    "context:compress": "node ./scripts/repomix-llm.mjs --config repomix.config.json .",
    "context:headroom": "node ./scripts/repomix-llm.mjs --config repomix.config.json --headroom-only .",
    "headroom:proxy": "bash ./scripts/headroom-proxy-dev.sh",
    "validate:blueprints": "node ./scripts/validate-blueprints.mjs",
    "next:mcp:ws": "node ./scripts/next-mcp-ws-bridge.mjs",
    "next:mcp:ws:probe": "node ./scripts/next-mcp-ws-probe.mjs",
    "next:mcp:ws:smoke": "node ./scripts/next-mcp-ws-smoke.mjs",
    "build": "next build --webpack",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "check": "npm run lint && npm run typecheck && npm run build",
    "test": "vitest",
    "test:coding-regression": "python -m pytest -q source_proxy/tests/test_coding_regression_pack.py",
    "test:coding-frontend-regression": "vitest run src/app/coding/__tests__/page.test.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx src/lib/coding/__tests__/model-provider-status.test.ts src/lib/coding/__tests__/unified-diff-paths.test.ts src/components/coding/__tests__/approval-gate-binding.test.ts src/lib/coding/__tests__/proxy-route-payload.test.ts src/app/v1/actions/execute-approved/__tests__/route.test.ts src/components/coding/__tests__/coding-workflow-step.test.ts src/components/coding/__tests__/client-fallback.test.ts src/components/coding/__tests__/proxy-safety-smoke.test.ts src/app/v1/coding/self-tests/run/__tests__/route.test.ts",
    "test:ui": "vitest --ui",
    "ytmclone:stats:smoke": "node ./scripts/ytmclone-stats-smoke.mjs",
    "ytmclone:android:build": "cd apps/ytmclone-android && ./gradlew assembleDebug",
    "postinstall": "node ./scripts/postinstall-repomix-shim.mjs"
  },
  "dependencies": {
    "@ai-sdk/openai": "^3.0.58",
    "@ai-sdk/react": "^3.0.176",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "ai": "^6.0.174",
    "clsx": "^2.1.1",
    "dexie": "^4.4.2",
    "dexie-react-hooks": "^4.4.0",
    "framer-motion": "^12.38.0",
    "headroom-ai": "^0.22.4",
    "hls.js": "^1.6.16",
    "lucide-react": "^1.8.0",
    "next": "16.2.4",
    "react": "19.2.4",
    "react-dom": "19.2.4",
    "react-markdown": "^10.1.0",
    "remark-gfm": "^4.0.1",
    "server-only": "^0.0.1",
    "swr": "^2.4.1",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@modelcontextprotocol/sdk": "^1.24.3",
    "@playwright/test": "^1.60.0",
    "@tailwindcss/postcss": "^4",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "@vitejs/plugin-react": "^6.0.1",
    "@vitest/ui": "^4.1.5",
    "eslint": "^9",
    "eslint-config-next": "16.2.4",
    "jsdom": "^24.1.3",
    "next-devtools-mcp": "^0.3.10",
    "repomix": "^1.14.0",
    "tailwindcss": "^4",
    "typescript": "^5",
    "vitest": "^4.1.5",
    "ws": "^8.20.0"
  }
}
===== package-lock.json
{
  "name": "spirit-os",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "spirit-os",
      "version": "0.1.0",
      "dependencies": {
        "@ai-sdk/openai": "^3.0.58",
        "@ai-sdk/react": "^3.0.176",
        "@dnd-kit/core": "^6.3.1",
        "@dnd-kit/sortable": "^10.0.0",
        "@dnd-kit/utilities": "^3.2.2",
        "ai": "^6.0.174",
        "clsx": "^2.1.1",
        "dexie": "^4.4.2",
        "dexie-react-hooks": "^4.4.0",
        "framer-motion": "^12.38.0",
        "headroom-ai": "^0.22.4",
        "hls.js": "^1.6.16",
        "lucide-react": "^1.8.0",
        "next": "16.2.4",
        "react": "19.2.4",
        "react-dom": "19.2.4",
        "react-markdown": "^10.1.0",
        "remark-gfm": "^4.0.1",
        "server-only": "^0.0.1",
        "swr": "^2.4.1",
        "tailwind-merge": "^3.5.0"
      },
      "bin": {
        "repomix": "scripts/repomix-llm.mjs"
      },
      "devDependencies": {
        "@modelcontextprotocol/sdk": "^1.24.3",
        "@playwright/test": "^1.60.0",
        "@tailwindcss/postcss": "^4",
        "@testing-library/jest-dom": "^6.9.1",
        "@testing-library/react": "^16.3.2",
        "@types/node": "^20",
        "@types/react": "^19",
        "@types/react-dom": "^19",
        "@vitejs/plugin-react": "^6.0.1",
        "@vitest/ui": "^4.1.5",
        "eslint": "^9",
        "eslint-config-next": "16.2.4",
        "jsdom": "^24.1.3",
        "next-devtools-mcp": "^0.3.10",
        "repomix": "^1.14.0",
        "tailwindcss": "^4",
        "typescript": "^5",
        "vitest": "^4.1.5",
        "ws": "^8.20.0"
      }
    },
    "node_modules/@adobe/css-tools": {
      "version": "4.4.4",
      "resolved": "https://registry.npmjs.org/@adobe/css-tools/-/css-tools-4.4.4.tgz",
      "integrity": "sha512-Elp+iwUx5rN5+Y8xLt5/GRoG20WGoDCQ/1Fb+1LiGtvwbDavuSk0jhD/eZdckHAuzcDzccnkv+rEjyWfRx18gg==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@ai-sdk/gateway": {
      "version": "3.0.109",
      "resolved": "https://registry.npmjs.org/@ai-sdk/gateway/-/gateway-3.0.109.tgz",
      "integrity": "sha512-r6dOqThjODp1vOhGRJg2OCmyB/ZOQtGx1esZ2SDvwDX5XoX8dBqYaYjLg8MPXTzMGJSgOkJyCxWgUcZtAl16pw==",
      "license": "Apache-2.0",
      "dependencies": {
        "@ai-sdk/provider": "3.0.10",
        "@ai-sdk/provider-utils": "4.0.26",
        "@vercel/oidc": "3.2.0"
      },
      "engines": {
        "node": ">=18"
      },
      "peerDependencies": {
        "zod": "^3.25.76 || ^4.1.8"
      }
    },
    "node_modules/@ai-sdk/openai": {
      "version": "3.0.58",
      "resolved": "https://registry.npmjs.org/@ai-sdk/openai/-/openai-3.0.58.tgz",
      "integrity": "sha512-2+5xGMROmrBboJuoOwqLL3b/o3i56+NRdxXDNVAiTyYjLiBj6KzembeuyuBT217be1X+zkEfAqD1H0irJlGIyw==",
      "license": "Apache-2.0",
      "dependencies": {
        "@ai-sdk/provider": "3.0.10",
        "@ai-sdk/provider-utils": "4.0.26"
      },
      "engines": {
        "node": ">=18"
      },
      "peerDependencies": {
        "zod": "^3.25.76 || ^4.1.8"
      }
    },
    "node_modules/@ai-sdk/provider": {
      "version": "3.0.10",
      "resolved": "https://registry.npmjs.org/@ai-sdk/provider/-/provider-3.0.10.tgz",
      "integrity": "sha512-Q3BZ27qfpYqnCYGvE3vt+Qi6LGOF9R5Nmzn+9JoM1lCRsD9mYaIhfJLkSunN48nfGXJ6n+XNV0J/XVpqGQl7Dw==",
      "license": "Apache-2.0",
      "dependencies": {
        "json-schema": "^0.4.0"
      },
      "engines": {
        "node": ">=18"
      }
    },
    "node_modules/@ai-sdk/provider-utils": {
      "version": "4.0.26",
      "resolved": "https://registry.npmjs.org/@ai-sdk/provider-utils/-/provider-utils-4.0.26.tgz",
      "integrity": "sha512-CsKNLKsOpvPujRlIYvoz+Ybw+kGn7J4/fIZa/58+R7iWLLfwn6ifE2G6Yq8K9XvH/I/3bzaDAJ3NhRwEMsLBKQ==",
      "license": "Apache-2.0",
      "dependencies": {
        "@ai-sdk/provider": "3.0.10",
        "@standard-schema/spec": "^1.1.0",
        "eventsource-parser": "^3.0.8"
      },
      "engines": {
        "node": ">=18"
      },
      "peerDependencies": {
        "zod": "^3.25.76 || ^4.1.8"
      }
    },
    "node_modules/@ai-sdk/react": {
      "version": "3.0.176",
      "resolved": "https://registry.npmjs.org/@ai-sdk/react/-/react-3.0.176.tgz",
      "integrity": "sha512-8CKMdSJDAHHUYEJSsI+HGanP/75dOYtnLWQ5WtQMvdmsA4PUVy8Hv6Bn1npoZBcTh250ESsuSptvctxFuIJrYw==",
      "license": "Apache-2.0",
      "dependencies": {
        "@ai-sdk/provider-utils": "4.0.26",
        "ai": "6.0.174",
        "swr": "^2.2.5",
        "throttleit": "2.1.0"
      },
      "engines": {
        "node": ">=18"
      },
      "peerDependencies": {
        "react": "^18 || ~19.0.1 || ~19.1.2 || ^19.2.1"
      }
    },
    "node_modules/@alloc/quick-lru": {
      "version": "5.2.0",
      "resolved": "https://registry.npmjs.org/@alloc/quick-lru/-/quick-lru-5.2.0.tgz",
      "integrity": "sha512-UrcABB+4bUrFABwbluTIBErXwvbsU/V7TZWfmbgJfbkwiBuziS9gxdODUyuiecfdGQ85jglMW6juS3+z5TsKLw==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/sponsors/sindresorhus"
      }
    },
    "node_modules/@asamuzakjp/css-color": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/@asamuzakjp/css-color/-/css-color-3.2.0.tgz",
      "integrity": "sha512-K1A6z8tS3XsmCMM86xoWdn7Fkdn9m6RSVtocUrJYIwZnFVkng/PvkEoWtOWmP+Scc6saYWHWZYbndEEXxl24jw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@csstools/css-calc": "^2.1.3",
        "@csstools/css-color-parser": "^3.0.9",
        "@csstools/css-parser-algorithms": "^3.0.4",
        "@csstools/css-tokenizer": "^3.0.3",
        "lru-cache": "^10.4.3"
      }
    },
    "node_modules/@asamuzakjp/css-color/node_modules/lru-cache": {
      "version": "10.4.3",
      "resolved": "https://registry.npmjs.org/lru-cache/-/lru-cache-10.4.3.tgz",
      "integrity": "sha512-JNAzZcXrCt42VGLuYz0zfAzDfAvJWW6AfYlDBQyDV5DClI2m5sAmK+OIO7s59XfsRsWHp02jAJrRadPRGTt6SQ==",
      "dev": true,
      "license": "ISC"
    },
    "node_modules/@babel/code-frame": {
      "version": "7.29.0",
      "resolved": "https://registry.npmjs.org/@babel/code-frame/-/code-frame-7.29.0.tgz",
      "integrity": "sha512-9NhCeYjq9+3uxgdtp20LSiJXJvN0FeCtNGpJxuMFZ1Kv3cWUNb6DOhJwUvcVCzKGR66cw4njwM6hrJLqgOwbcw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@babel/helper-validator-identifier": "^7.28.5",
        "js-tokens": "^4.0.0",
        "picocolors": "^1.1.1"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/compat-data": {
      "version": "7.29.3",
      "resolved": "https://registry.npmjs.org/@babel/compat-data/-/compat-data-7.29.3.tgz",
      "integrity": "sha512-LIVqM46zQWZhj17qA8wb4nW/ixr2y1Nw+r1etiAWgRM6U1IqP+LNhL1yg440jYZR72jCWcWbLWzIosH+uP1fqg==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/core": {
      "version": "7.29.0",
      "resolved": "https://registry.npmjs.org/@babel/core/-/core-7.29.0.tgz",
      "integrity": "sha512-CGOfOJqWjg2qW/Mb6zNsDm+u5vFQ8DxXfbM09z69p5Z6+mE1ikP2jUXw+j42Pf1XTYED2Rni5f95npYeuwMDQA==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@babel/code-frame": "^7.29.0",
        "@babel/generator": "^7.29.0",
        "@babel/helper-compilation-targets": "^7.28.6",
        "@babel/helper-module-transforms": "^7.28.6",
        "@babel/helpers": "^7.28.6",
        "@babel/parser": "^7.29.0",
        "@babel/template": "^7.28.6",
        "@babel/traverse": "^7.29.0",
        "@babel/types": "^7.29.0",
        "@jridgewell/remapping": "^2.3.5",
```

## Cleanup / Archive / Watch / Health Script Candidates

```
config/backup.env.example
docs/backup-system/backup-system-v0.1-contract.md
docs/backup-system/backup-system-v0.1-master-status.md
docs/backup-system/backup-system-v0.1-next-gates.md
docs/backup-system/backup-system-v0.1-plan.md
docs/backup-system/backup-system-v0.1-scheduler-install-checklist.md
docs/backup-system/backup-system-v0.1-scheduler-readiness.md
docs/backup-system/first-backup-approval-packet.md
docs/backup-system/mac-node-first-backup-approval-packet.md
docs/backup-system/operator-next-approval-packet.md
docs/backup-system/restore-drill-checklist.md
docs/backup-system/templates/spiritos-backup-dell.service.example
docs/backup-system/templates/spiritos-backup-dell.timer.example
docs/backup-system/templates/spiritos-backup-mac-launchd.plist.example
docs/backup-system/templates/spiritos-backup-windows-task.xml.example
docs/backup-system/windows-node-first-backup-approval-packet.md
docs/cartographer-full-auto-plan-1-step-3-1-restart-dev-server-and-rerun-read-only-map-browser-acceptance.md
docs/cartographer-level-10-project-health-timeline.md
docs/cartographer-level-14-recurring-health-check-boundary.md
docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/final-ui-cleanup-2026-05-28.md
docs/evidence/backup-system/backup-system-v0.1-closeout.md
docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md
docs/evidence/backup-system/db-docker-volume-backup/increment-1.1-preflight.md
docs/evidence/backup-system/db-docker-volume-backup/increment-1.2-state-classification.md
docs/evidence/backup-system/db-docker-volume-backup/increment-1.3-staging-directories.md
docs/evidence/backup-system/db-docker-volume-backup/increment-2.1-db-discovery.md
docs/evidence/backup-system/db-docker-volume-backup/increment-2.2-postgres-logical-dump.md
docs/evidence/backup-system/db-docker-volume-backup/increment-2.3-db-dumps-restic-backup.md
docs/evidence/backup-system/db-docker-volume-backup/increment-2.4-db-dump-verify.md
docs/evidence/backup-system/db-docker-volume-backup/increment-3.1-volume-size-check.md
docs/evidence/backup-system/db-docker-volume-backup/increment-3.2-volume-export.md
docs/evidence/backup-system/db-docker-volume-backup/increment-3.3-volume-exports-restic-backup.md
docs/evidence/backup-system/db-docker-volume-backup/increment-3.4-volume-export-verify.md
docs/evidence/backup-system/db-docker-volume-backup/increment-4.1-db-dump-restore-proof.md
docs/evidence/backup-system/db-docker-volume-backup/increment-4.2-volume-export-restore-proof.md
docs/evidence/backup-system/db-docker-volume-backup/phase-1-closeout.md
docs/evidence/backup-system/db-docker-volume-backup/phase-2-closeout.md
docs/evidence/backup-system/db-docker-volume-backup/phase-3-closeout.md
docs/evidence/backup-system/db-docker-volume-backup/phase-4-closeout.md
docs/evidence/backup-system/first-real-dell-backup/first-real-dell-backup-closeout-final.md
docs/evidence/backup-system/first-real-dell-backup/first-real-dell-backup-closeout.md
docs/evidence/backup-system/first-real-dell-backup/first-real-dell-backup-closeout-resumed.md
docs/evidence/backup-system/first-real-dell-backup/increment-1.1-preflight.md
docs/evidence/backup-system/first-real-dell-backup/increment-1.2-8tb-mount.md
docs/evidence/backup-system/first-real-dell-backup/increment-1.3-restic-availability.md
docs/evidence/backup-system/first-real-dell-backup/increment-1.3R-restic-installed-after-manual-sudo.md
docs/evidence/backup-system/first-real-dell-backup/increment-2.1-directory-create.md
docs/evidence/backup-system/first-real-dell-backup/increment-2.1R-directory-permission-fixed.md
docs/evidence/backup-system/first-real-dell-backup/increment-2.2R-restic-password-file-check.md
docs/evidence/backup-system/first-real-dell-backup/increment-2.3R-restic-init.md
docs/evidence/backup-system/first-real-dell-backup/increment-3.1R-final-dry-run.md
docs/evidence/backup-system/first-real-dell-backup/increment-3.2R-first-real-backup.md
docs/evidence/backup-system/first-real-dell-backup/increment-4.1R-restore-drill.md
docs/evidence/backup-system/first-real-dell-backup/phase-1-closeout.md
docs/evidence/backup-system/first-real-dell-backup/phase-2-closeout.md
docs/evidence/backup-system/first-real-dell-backup/phase-2-resumed-closeout.md
docs/evidence/backup-system/first-real-dell-backup/phase-3-resumed-closeout.md
docs/evidence/backup-system/first-real-dell-backup/phase-4-resumed-closeout.md
docs/evidence/backup-system/mac-node-backup/increment-1.1-mac-preflight.md
docs/evidence/backup-system/mac-node-backup/increment-1.1R-mac-restic-confirmed.md
docs/evidence/backup-system/mac-node-backup/increment-1.2-mac-restic-install-attempt.md
docs/evidence/backup-system/mac-node-backup/increment-1.2R-dell-staging-path.md
docs/evidence/backup-system/mac-node-backup/increment-2.1R-mac-pull-dry-run.md
docs/evidence/backup-system/mac-node-backup/increment-2.2R-mac-pull-real.md
docs/evidence/backup-system/mac-node-backup/increment-3.1R-mac-staging-restic-backup.md
docs/evidence/backup-system/mac-node-backup/increment-3.2R-mac-restore-proof.md
docs/evidence/backup-system/mac-node-backup/mac-node-backup-closeout-final.md
docs/evidence/backup-system/mac-node-backup/mac-node-backup-closeout.md
docs/evidence/backup-system/mac-node-backup/phase-1-resumed-closeout.md
docs/evidence/backup-system/mac-node-backup/phase-2-resumed-closeout.md
docs/evidence/backup-system/mac-node-backup/phase-3-resumed-closeout.md
docs/evidence/backup-system/master-closeout/backup-system-v0.1-master-closeout.md
docs/evidence/backup-system/master-closeout/increment-1.1-evidence-baseline.md
docs/evidence/backup-system/master-closeout/increment-1.2-closeout-file-verification.md
docs/evidence/backup-system/master-closeout/increment-1.3-result-matrix.md
docs/evidence/backup-system/master-closeout/increment-2.1-restic-snapshot-inventory.md
docs/evidence/backup-system/master-closeout/increment-2.2-restic-check.md
docs/evidence/backup-system/master-closeout/increment-2.3-staging-and-restore-inventory.md
docs/evidence/backup-system/master-closeout/increment-3.1-master-status.md
docs/evidence/backup-system/master-closeout/increment-3.2-scheduler-readiness.md
docs/evidence/backup-system/master-closeout/increment-3.3-next-gates.md
docs/evidence/backup-system/master-closeout/increment-4.1-scheduler-template-audit.md
docs/evidence/backup-system/master-closeout/increment-4.2-scheduler-install-checklist.md
docs/evidence/backup-system/master-closeout/phase-1-closeout.md
docs/evidence/backup-system/master-closeout/phase-2-closeout.md
docs/evidence/backup-system/master-closeout/phase-3-closeout.md
docs/evidence/backup-system/master-closeout/phase-4-closeout.md
docs/evidence/backup-system/plan-1/increment-1.1.1-evidence-root.md
docs/evidence/backup-system/plan-1/increment-1.1.2-repo-path-inventory.md
docs/evidence/backup-system/plan-1/increment-1.1.3-docker-state-inventory.md
docs/evidence/backup-system/plan-1/increment-1.1.4-node-inventory.md
docs/evidence/backup-system/plan-1/phase-1.1-closeout.md
docs/evidence/backup-system/plan-1/phase-1.2-closeout.md
docs/evidence/backup-system/plan-2/increment-2.1.1-shared-library.md
docs/evidence/backup-system/plan-2/increment-2.1.2-inventory-script.md
docs/evidence/backup-system/plan-2/increment-2.1.3-manifest-generator.md
docs/evidence/backup-system/plan-2/phase-2.1-closeout.md
docs/evidence/backup-system/plan-3/increment-3.1.1-dell-restic-wrapper.md
docs/evidence/backup-system/plan-3/increment-3.1.2-dell-approval-packet.md
docs/evidence/backup-system/plan-3/phase-3.1-closeout.md
docs/evidence/backup-system/plan-4/increment-4.1.1-database-planner.md
docs/evidence/backup-system/plan-4/increment-4.1.2-docker-volume-planner.md
docs/evidence/backup-system/plan-4/phase-4.1-closeout.md
docs/evidence/backup-system/plan-5/increment-5.1.1-mac-planner.md
docs/evidence/backup-system/plan-5/increment-5.1.2-mac-approval-packet.md
docs/evidence/backup-system/plan-5/phase-5.1-closeout.md
docs/evidence/backup-system/plan-6/increment-6.1.1-windows-planner.md
docs/evidence/backup-system/plan-6/increment-6.1.2-windows-approval-packet.md
docs/evidence/backup-system/plan-6/phase-6.1-closeout.md
docs/evidence/backup-system/plan-7/increment-7.1.1-restore-helper.md
docs/evidence/backup-system/plan-7/increment-7.1.2-restore-checklist.md
docs/evidence/backup-system/plan-7/phase-7.1-closeout.md
docs/evidence/backup-system/plan-8/increment-8.1.1-systemd-templates.md
docs/evidence/backup-system/plan-8/increment-8.1.2-node-scheduler-templates.md
docs/evidence/backup-system/plan-8/phase-8.1-closeout.md
docs/evidence/backup-system/plan-9/full-closeout.md
docs/evidence/backup-system/plan-9/increment-9.1.1-final-validation.md
docs/evidence/backup-system/plan-9/increment-9.1.2-final-packets.md
docs/evidence/backup-system/plan-9/phase-9.1-closeout.md
docs/evidence/backup-system/restore-drill-repair/increment-1.1-snapshot-path-inspection.md
docs/evidence/backup-system/restore-drill-repair/increment-1.2-helper-inspection.md
docs/evidence/backup-system/restore-drill-repair/increment-2.1-helper-patch.md
docs/evidence/backup-system/restore-drill-repair/increment-2.2-dry-run.md
docs/evidence/backup-system/restore-drill-repair/increment-3.1-real-restore-drill.md
docs/evidence/backup-system/restore-drill-repair/increment-3.2-restored-file-verification.md
docs/evidence/backup-system/restore-drill-repair/phase-1-closeout.md
docs/evidence/backup-system/restore-drill-repair/phase-2-closeout.md
docs/evidence/backup-system/restore-drill-repair/phase-3-closeout.md
docs/evidence/backup-system/restore-drill-repair/restore-drill-repair-closeout.md
docs/evidence/backup-system/windows-node-backup/increment-1.1-windows-gate-preflight.md
docs/evidence/backup-system/windows-node-backup/increment-1.2-windows-sftp-dry-run-preflight.md
docs/evidence/backup-system/windows-node-backup/increment-1.3-windows-restic-repo-init.md
docs/evidence/backup-system/windows-node-backup/increment-2.1-windows-first-real-backup.md
docs/evidence/backup-system/windows-node-backup/increment-2.2-windows-restore-proof-attempt-1.md
docs/evidence/backup-system/windows-node-backup/increment-2.3-windows-restore-proof-go.md
docs/evidence/backup-system/windows-node-backup/windows-node-backup-closeout-final.md
docs/evidence/backup-system/windows-node-backup/windows-node-backup-closeout.md
docs/evidence/coding-human-trial-runner-polish/worktree-cleanup.md
docs/evidence/coding-live-runner-final/10-worktree-cleanup.md
docs/evidence/coding-reversible-trial-runner-suite/09-worktree-cleanup.md
docs/evidence/hermes4-full-integration/increment-4.1-spirit-health.md
docs/evidence/hermes4-full-integration/increment-4.2-source-proxy-health-status.md
docs/evidence/media-face-organizer-source-of-truth-plan-20260614/ui-ux-cleanup-spec.md
docs/evidence/media-server/phase-5/increment-5.1-backup-classification.md
docs/evidence/repo-host-cleanup-stability-audit-20260617/00-git-status.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/00-preflight.md
docs/evidence/repo-host-cleanup-stability-audit-20260617/00-system-baseline.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_date_is.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_df_h.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_free_h.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_head.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_status.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_toplevel.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_worktree.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_hostname.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_last_x_head.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_pwd.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_uptime.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_who_b.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_artifact_names.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_du_depth2.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_count.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_groups.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_extension_counts.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_file_count.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_top_level_counts.txt
docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_gitignore.txt
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-05-timer-fip0-1a62da032a749280.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-05-timer-fip0-39bf6f511eac8e3a.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-05-timer-fip0-a63f06040d5038af.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-05-stopwatch-fip0-1f18517e2913bfbe.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-05-stopwatch-fip0-2e5d328f73756e68.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-10-health-fip0-a68f4bd6733e9802.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-10-health-fip0-a8f965eecd5b94f8.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/set1/s1-05-timer/timer.js
docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/set2/s2-05-stopwatch/stopwatch.js
docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/set2/s2-10-health/health.ts
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-05-timer-fip0-1a62da032a749280.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-05-timer-fip0-39bf6f511eac8e3a.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-05-timer-fip0-a63f06040d5038af.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-05-stopwatch-fip0-1f18517e2913bfbe.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-05-stopwatch-fip0-2e5d328f73756e68.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-10-health-fip0-a68f4bd6733e9802.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-10-health-fip0-a8f965eecd5b94f8.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/verification-truth-cleanup-smoke/receipt-fip0-b6c23ffc2301721c.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/verification-truth-cleanup-smoke/summary.json
docs/evidence/source-proxy-claude-3x10-audit-20260615/verification-truth-cleanup-smoke/trace-fip0-b6c23ffc2301721c.json
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/bin/watchfiles
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/aider/__pycache__/watch.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/aider/__pycache__/watch_prompts.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/aider/watch_prompts.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/aider/watch.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/aider/website/docs/usage/watch.md
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/fsspec/archive.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/fsspec/implementations/libarchive.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/fsspec/implementations/__pycache__/libarchive.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/fsspec/__pycache__/archive.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/litellm_core_utils/audio_utils/audio_health_check.wav
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/litellm_core_utils/health_check_helpers.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/litellm_core_utils/health_check_utils.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/litellm_core_utils/__pycache__/health_check_helpers.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/litellm_core_utils/__pycache__/health_check_utils.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/llms/custom_httpx/async_client_cleanup.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/llms/custom_httpx/__pycache__/async_client_cleanup.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/model_prices_and_context_window_backup.json
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/client/health.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/client/__pycache__/health.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/db/db_transaction_queue/__pycache__/spend_log_cleanup.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/db/db_transaction_queue/spend_log_cleanup.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/example_config_yaml/_health_check_test_config.yaml
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/.gitignore
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_check.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_check_utils/__init__.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_check_utils/__pycache__/__init__.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_check_utils/__pycache__/shared_health_check_manager.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_check_utils/shared_health_check_manager.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_endpoints/health_app_factory.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_endpoints/_health_endpoints.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_endpoints/__pycache__/health_app_factory.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/health_endpoints/__pycache__/_health_endpoints.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/proxy/__pycache__/health_check.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/types/integrations/base_health_check.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/litellm/types/integrations/__pycache__/base_health_check.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/numpy/ma/__pycache__/timer_comparison.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/numpy/ma/timer_comparison.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/hyperscan/gitignore.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/hyperscan/__pycache__/gitignore.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/re2/gitignore.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/re2/__pycache__/gitignore.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/simple/gitignore.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/_backends/simple/__pycache__/gitignore.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/gitignore.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/base.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/basic.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/__init__.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/__pycache__/base.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/__pycache__/basic.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/__pycache__/__init__.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/__pycache__/spec.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/patterns/gitignore/spec.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pathspec/__pycache__/gitignore.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pip/_vendor/rich/__pycache__/_timer.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/pip/_vendor/rich/_timer.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/rich/__pycache__/_timer.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/rich/_timer.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/tqdm/_monitor.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/tqdm/__pycache__/_monitor.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/tree_sitter_language_pack/bindings/gitignore.abi3.so
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/entry_points.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/INSTALLER
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/licenses/LICENSE
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/METADATA
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/RECORD
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles-1.1.1.dist-info/WHEEL
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/cli.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/filters.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__init__.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__main__.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/main.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/cli.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/filters.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/__init__.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/__main__.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/main.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/run.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/__pycache__/version.cpython-312.pyc
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/py.typed
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/run.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/_rust_notify.cpython-312-x86_64-linux-gnu.so
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/_rust_notify.pyi
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/lib/python3.12/site-packages/watchfiles/version.py
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-file-edit-stress-test/continue-default/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-file-edit-stress-test/continue-gpt4o-mini/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-file-edit-stress-test/continue-hermes4/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-qwen-real-env-debug/continue-qwen/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/file-edit-model-shell-gauntlet/cleanup-note.md
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/lane-plumbing-repair/continue-qwen-bridged/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/native-continue-api-smoke/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/native-continue-gemma-smoke/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/native-continue-hermes4-smoke/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/native-continue-qwen-smoke/workspace/.git/hooks/fsmonitor-watchman.sample
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/plan-3-cleanup-stabilization-closeout.md
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/anti-cheat-report.json
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/closeout.md
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/continue-qwen-config.yaml
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/aider-version.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/continue-version.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/docker-ollama.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/env-gate.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/nvidia-smi.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/ollama-list.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/ollama-ps.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/ps-ollama.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/qwen-http-readiness.json
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/environment/system-ollama.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/http-server.log
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/http-server.pid
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/index.html
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/lanes/aider-qwen-after-cleanup/command-log.txt
docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest/lanes/aider-qwen-after-cleanup/diff-after-run.patch
```

## Tracked Top-Level Distribution

```
   6362 docs
   1942 scripts
    802 src
    321 source_proxy
    159 scout
     38 _blueprints
     25 tests
     23 data
     13 apps
     12 .codex-smoke
     11 _reference
      7 backend
      5 public
      5 chatDesign
      4 config
      2 services
      1 vitest.config.mjs
      1 v1prepPlan.md
      1 tsconfig.json
      1 Transparent-ref2.png
      1 spiritos-chat-demo.zip
      1 spiritBlueprinter.md
      1 scouUi.md
      1 scoutRefinemint.md
      1 scout0.2-0.3.md
      1 requirements.txt
      1 requirements.cuda.txt
      1 requirements.core.txt
      1 .repomixignore
      1 repomix.config.json
      1 README.md
      1 .python-version
      1 productionProxy.md
      1 post-v1-diag.md
      1 postcss.config.mjs
      1 playwright.config.mjs
      1 package-lock.json
      1 package.json
      1 notes.md
      1 nohup.out
      1 next-env.d.ts
      1 next.config.ts
      1 middleware.ts
      1 masterOverhual.md
      1 .gitignore
      1 .gate
      1 eslint.config.mjs
      1 .env.local.example
      1 .env.example
      1 DEPENDENCY_AUDIT.md
      1 codingAgentOverhaul.md
      1 cartogrpaherPlanAuto.md
      1 cartographerBeta.md
      1 basic.js
      1 allowed-dev-origins.ts
      1 allowed-dev-origins.test.ts
      1 ai_runtime
```

## Untracked Top-Level Distribution

```
     46 docs
      6 src
      4 scripts
```

## Findings

- The repo has substantial evidence and generated-artifact surface area; `docs/evidence` should be kept as historical evidence but likely excluded from active repomix context once Britton approves.
- Any `.gitignore` or `repomix.config.*` changes are source/config changes and were not made.
- Cleanup/archive scripts exist or are referenced above; they should be reviewed before inventing new cleanup behavior.
