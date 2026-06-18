# S6 Staged Files

## Verification

The staged set was inspected after exact-path `git add`. It contains only eligible S6 files and S6 evidence.

Watcher files/evidence were not staged. Source Proxy evidence/files were not staged. Media/face-organizer files were not staged. Repomix/headroom/tooling files were not staged. Package files were not staged.

## `git diff --cached --name-status`

```text
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/00-baseline.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/00-preflight.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/10-s6-implementation-review.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/20-test-results.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/30-browser-smoke.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/40-safety-audit.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/99-final-git-status.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/final-verdict.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/index.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/operator-summary.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-devserver-status.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-error.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-exit-code.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-result.json
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-stderr.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/browser-smoke-stdout.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/dev-server-3002-tail.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/dev-server-3002.pid
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/existing-3000-probe.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/s6-smoke.cjs
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/browser/spiritflix-admin-s6-smoke.png
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/s6-commit-verification/home-player-vitest.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/s6-commit-verification/safety-scan.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/s6-commit-verification/smart-admin-api-vitest.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/s6-commit-verification/typecheck.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/safety-rg-local-bin.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/safety-rg.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/01-typecheck.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/02-vitest-admin-smart.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/03-vitest-home-player.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/04-rerun-typecheck.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/05-rerun-vitest-admin-smart.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/06-rerun-vitest-home-player.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/exit-codes.txt
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/raw/tests/rerun-exit-codes.json
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-file-list.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-preflight.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-safety-scan.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-verification.md
A	docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/summary.json
M	docs/media/spiritflix-smart-tagging-rename-plan.md
M	src/app/api/spiritflix/admin/smart/analysis/route.ts
M	src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
M	src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx
A	src/lib/spiritflix/admin/smart/__tests__/metadata-bridge.test.ts
A	src/lib/spiritflix/admin/smart/__tests__/rename-preview.test.ts
M	src/lib/spiritflix/admin/smart/index.ts
A	src/lib/spiritflix/admin/smart/metadata-bridge.ts
A	src/lib/spiritflix/admin/smart/rename-preview.ts
M	src/styles/spiritflix.css
```

## `git diff --cached --stat`

```text
 .../00-baseline.txt                                |  139 ++
 .../00-preflight.md                                |  143 ++
 .../10-s6-implementation-review.md                 |   33 +
 .../20-test-results.md                             |   28 +
 .../30-browser-smoke.md                            |   52 +
 .../40-safety-audit.md                             |   35 +
 .../99-final-git-status.txt                        |   92 +
 .../final-verdict.md                               |   39 +
 .../index.md                                       |   23 +
 .../operator-summary.md                            |   11 +
 .../raw/browser/browser-smoke-devserver-status.txt |    1 +
 .../raw/browser/browser-smoke-error.txt            |    8 +
 .../raw/browser/browser-smoke-exit-code.txt        |    1 +
 .../raw/browser/browser-smoke-result.json          |   15 +
 .../raw/browser/browser-smoke-stderr.txt           |    0
 .../raw/browser/browser-smoke-stdout.txt           |   15 +
 .../raw/browser/dev-server-3002-tail.txt           |   18 +
 .../raw/browser/dev-server-3002.pid                |    1 +
 .../raw/browser/existing-3000-probe.txt            |   71 +
 .../raw/browser/s6-smoke.cjs                       |  147 ++
 .../raw/browser/spiritflix-admin-s6-smoke.png      |  Bin 0 -> 123960 bytes
 .../s6-commit-verification/home-player-vitest.txt  |   17 +
 .../raw/s6-commit-verification/safety-scan.txt     |  234 +++
 .../smart-admin-api-vitest.txt                     |  130 ++
 .../raw/s6-commit-verification/typecheck.txt       |    4 +
 .../raw/safety-rg-local-bin.txt                    |  237 +++
 .../raw/safety-rg.txt                              |    4 +
 .../raw/tests/01-typecheck.txt                     |    4 +
 .../raw/tests/02-vitest-admin-smart.txt            | 2183 ++++++++++++++++++++
 .../raw/tests/03-vitest-home-player.txt            |   17 +
 .../raw/tests/04-rerun-typecheck.txt               |    7 +
 .../raw/tests/05-rerun-vitest-admin-smart.txt      |  137 ++
 .../raw/tests/06-rerun-vitest-home-player.txt      |   20 +
 .../raw/tests/exit-codes.txt                       |    3 +
 .../raw/tests/rerun-exit-codes.json                |    8 +
 .../s6-commit-file-list.md                         |   44 +
 .../s6-commit-preflight.md                         |  147 ++
 .../s6-commit-safety-scan.md                       |   34 +
 .../s6-commit-verification.md                      |   23 +
 .../summary.json                                   |   34 +
 docs/media/spiritflix-smart-tagging-rename-plan.md |   14 +
 .../api/spiritflix/admin/smart/analysis/route.ts   |   72 +-
 .../admin/SpiritFlixSmartReviewPanel.tsx           |  386 +++-
 .../__tests__/SpiritFlixSmartReviewPanel.test.tsx  |   79 +-
 .../admin/smart/__tests__/metadata-bridge.test.ts  |  140 ++
 .../admin/smart/__tests__/rename-preview.test.ts   |  114 +
 src/lib/spiritflix/admin/smart/index.ts            |   29 +
 src/lib/spiritflix/admin/smart/metadata-bridge.ts  |  142 ++
 src/lib/spiritflix/admin/smart/rename-preview.ts   |  145 ++
 src/styles/spiritflix.css                          |   99 +
 50 files changed, 5341 insertions(+), 38 deletions(-)
```
