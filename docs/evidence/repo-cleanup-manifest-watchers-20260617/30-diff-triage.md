# Diff Triage Without Editing

## `README.md`
- exists: True
- diff stat: `README.md | 42 ++++++++++++++++++++++++++++++------------
 1 file changed, 30 insertions(+), 12 deletions(-)`

```diff
diff --git a/README.md b/README.md
index 2e85b452..ce431f18 100755
--- a/README.md
+++ b/README.md
@@ -675,3 +675,9 @@ The common mix-up: `npm run proxy:https:lan` starts only the API on **8787**. It

-Generate the full repository context bundle:
+Generate the **LLM handoff** bundle (Repomix Tree-sitter + optional Headroom pass):
+
+```bash
+npx repomix --config repomix.config.json .
+```
+
+Equivalent:

@@ -679,16 +685,17 @@ Generate the full repository context bundle:
 npm run context:pack
-npx repomix --config repomix.config.json
 ```

-Generate the Tree-sitter + Headroom compressed bundle for large-context model routing:
+**Output:** `repomix-output.xml` — drop this into any model. (~1 MB compressed vs ~300 MB raw.)
+
+SpiritOS overrides the local `repomix` bin so the familiar CLI shape runs the full pipeline instead of dumping an uncompressed megafile. Mirrors also land at `repomix-output.ast.xml` and `repomix-output.headroom.xml`.
+
+**Headroom** (extra token savings) needs the Python proxy on **8797** — not Source Proxy on 8787:

 ```bash
-npm run context:compress
+pip install "headroom-ai[proxy]"
+npm run headroom:proxy          # terminal 1 — http://127.0.0.1:8797
+npx repomix --config repomix.config.json .   # terminal 2
 ```

-The compressed command writes `repomix-output.ast.xml` with a strict XML envelope.
-It also writes `repomix-output.headroom.xml` as a Headroom-specific review copy.
-If a local Headroom proxy is available at `HEADROOM_BASE_URL` (default `http://localhost:8787`),
-Headroom runs after Repomix and records savings in the `<headroom />` element.
-If the proxy is not running, the script falls back to the Repomix Tree-sitter payload.
+Or set `HEADROOM_API_KEY` for Headroom Cloud. Without a proxy, you still get Tree-sitter compression; the `<headroom />` element records `compressed="false"`.

@@ -696,3 +703,3 @@ If the proxy is not running, the script falls back to the Repomix Tree-sitter pa
 <system_directive>...</system_directive>
-<headroom compressed="true" tokens_saved="..." />
+<headroom compressed="true" tokens_saved="..." proxy="http://127.0.0.1:8797" />
 <repository_context format="repomix-xml">...</repository_context>
@@ -700,4 +707,9 @@ If the proxy is not running, the script falls back to the Repomix Tree-sitter pa

-Use `HEADROOM_CONTEXT_TOKEN_BUDGET` to tune the target context size, or rerun only
-the Headroom pass against the current AST bundle:
+Tune target size (default `80000` tokens):
+
+```bash
+HEADROOM_CONTEXT_TOKEN_BUDGET=60000 npx repomix --config repomix.config.json .
+```
+
+Re-run only the Headroom pass against the current AST bundle:

@@ -707,2 +719,8 @@ npm run context:headroom

+Raw uncompressed dump (legacy / debugging only):
+
+```bash
+npm run context:pack:full
+```
+
 ### Next MCP WebSocket diagnostics
```

## `package.json`
- exists: True
- diff stat: `package.json | 14 ++++++++++----
 1 file changed, 10 insertions(+), 4 deletions(-)`

```diff
diff --git a/package.json b/package.json
index 859ef303..c9ecae63 100755
--- a/package.json
+++ b/package.json
@@ -4,2 +4,5 @@
   "private": true,
+  "bin": {
+    "repomix": "./scripts/repomix-llm.mjs"
+  },
   "scripts": {
@@ -31,5 +34,7 @@
     "proxy:https:lan": "node ./scripts/source-proxy-dev.mjs --https --lan",
-    "context:pack": "repomix --config repomix.config.json .",
-    "context:compress": "node ./scripts/source-context-compress.mjs",
-    "context:headroom": "node ./scripts/source-context-compress.mjs --headroom-only",
+    "context:pack": "node ./scripts/repomix-llm.mjs --config repomix.config.json .",
+    "context:pack:full": "node ./scripts/repomix-llm.mjs --config repomix.config.json --full .",
+    "context:compress": "node ./scripts/repomix-llm.mjs --config repomix.config.json .",
+    "context:headroom": "node ./scripts/repomix-llm.mjs --config repomix.config.json --headroom-only .",
+    "headroom:proxy": "bash ./scripts/headroom-proxy-dev.sh",
     "validate:blueprints": "node ./scripts/validate-blueprints.mjs",
@@ -48,3 +53,4 @@
     "ytmclone:stats:smoke": "node ./scripts/ytmclone-stats-smoke.mjs",
-    "ytmclone:android:build": "cd apps/ytmclone-android && ./gradlew assembleDebug"
+    "ytmclone:android:build": "cd apps/ytmclone-android && ./gradlew assembleDebug",
+    "postinstall": "node ./scripts/postinstall-repomix-shim.mjs"
   },
```

## `package-lock.json`
- exists: True
- diff stat: `package-lock.json | 3 +++
 1 file changed, 3 insertions(+)`

```diff
diff --git a/package-lock.json b/package-lock.json
index 889881e0..d50f6006 100755
--- a/package-lock.json
+++ b/package-lock.json
@@ -32,2 +32,5 @@
       },
+      "bin": {
+        "repomix": "scripts/repomix-llm.mjs"
+      },
       "devDependencies": {
```

## `repomix.config.json`
- exists: True
- diff stat: `repomix.config.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)`

```diff
diff --git a/repomix.config.json b/repomix.config.json
index 7618c87e..d08db96a 100755
--- a/repomix.config.json
+++ b/repomix.config.json
@@ -6,3 +6,3 @@
   "output": {
-    "filePath": "repomix-output.xml",
+    "filePath": "repomix-output.full.xml",
     "style": "xml",
```

## `scripts/runtime-port-guard.sh`
- exists: True
- diff stat: `scripts/runtime-port-guard.sh | 26 ++++++++++++++++++++++++--
 1 file changed, 24 insertions(+), 2 deletions(-)`

```diff
diff --git a/scripts/runtime-port-guard.sh b/scripts/runtime-port-guard.sh
index b89c025f..8a8cbf91 100644
--- a/scripts/runtime-port-guard.sh
+++ b/scripts/runtime-port-guard.sh
@@ -92,2 +92,21 @@ kill_listeners_on_ports() {

+kill_spiritos_lan_listener_tree() {
+  local pid="$1"
+  local signal="${2:-TERM}"
+  local current="$pid"
+  local depth=0
+  local args
+
+  while [[ -n "$current" && "$current" != "1" && depth -lt 12 ]]; do
+    kill "-$signal" "$current" 2>/dev/null || true
+    pkill "-$signal" -P "$current" 2>/dev/null || true
+    args="$(ps -p "$current" -o args= 2>/dev/null || true)"
+    if is_spiritos_lan_dev_args "$args"; then
+      break
+    fi
+    current="$(ps -p "$current" -o ppid= 2>/dev/null | tr -d ' ')"
+    depth=$((depth + 1))
+  done
+}
+
 kill_spiritos_lan_listeners() {
@@ -99,3 +118,3 @@ kill_spiritos_lan_listeners() {
     if is_spiritos_lan_tree_pid "$pid"; then
-      kill -TERM "$pid" 2>/dev/null || true
+      kill_spiritos_lan_listener_tree "$pid" TERM
     else
@@ -104,2 +123,4 @@ kill_spiritos_lan_listeners() {
   done <<< "$port_pids"
+  # Orphaned next dev parents can survive listener-only kills and block restarts.
+  pkill -TERM -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
 }
@@ -113,5 +134,6 @@ force_kill_spiritos_lan_listeners() {
     if is_spiritos_lan_tree_pid "$pid"; then
-      kill -KILL "$pid" 2>/dev/null || true
+      kill_spiritos_lan_listener_tree "$pid" KILL
     fi
   done <<< "$port_pids"
+  pkill -KILL -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
 }
```

## `scripts/spiritos-lan-watchdog.sh`
- exists: True
- diff stat: `scripts/spiritos-lan-watchdog.sh | 13 ++++++++++++-
 1 file changed, 12 insertions(+), 1 deletion(-)`

```diff
diff --git a/scripts/spiritos-lan-watchdog.sh b/scripts/spiritos-lan-watchdog.sh
index a7a411b5..b19903ee 100644
--- a/scripts/spiritos-lan-watchdog.sh
+++ b/scripts/spiritos-lan-watchdog.sh
@@ -93,2 +93,3 @@ snapshot
 restart_count=0
+skip_next_cache_clear=0

@@ -96,3 +97,7 @@ while true; do
   stop_frontend_processes ""
-  if (( restart_count % CACHE_CLEAR_EVERY == 0 )); then
+  if (( skip_next_cache_clear )); then
+    log "skipping cache clear after fast-fail restart"
+    skip_next_cache_clear=0
+    rm -f .next/dev/lock 2>/dev/null || true
+  elif (( restart_count % CACHE_CLEAR_EVERY == 0 )); then
     clean_next_dev_cache
@@ -137,2 +142,8 @@ while true; do
     status=$?
+    if (( status == 1 )) && (( $(date +%s) - started_at < 45 )); then
+      log "frontend failed fast (likely EADDRINUSE); force-clearing :3000 listeners"
+      force_kill_spiritos_lan_listeners
+      wait_for_port_free 3000 15 || true
+      skip_next_cache_clear=1
+    fi
     log "frontend exited with status $status"
```

## `scripts/source-context-compress.mjs`
- exists: True
- diff stat: `scripts/source-context-compress.mjs | 272 +++++++++++++++++++++++++-----------
 1 file changed, 191 insertions(+), 81 deletions(-)`

```diff
diff --git a/scripts/source-context-compress.mjs b/scripts/source-context-compress.mjs
index 4e126d3e..f1b532cd 100755
--- a/scripts/source-context-compress.mjs
+++ b/scripts/source-context-compress.mjs
@@ -4,2 +4,3 @@ import { readFileSync, rmSync, writeFileSync } from "node:fs";
 import { resolve } from "node:path";
+import { fileURLToPath } from "node:url";
 import { compress } from "headroom-ai";
@@ -7,93 +8,195 @@ import { compress } from "headroom-ai";
 const repoRoot = resolve(import.meta.dirname, "..");
-const innerOutput = resolve(repoRoot, "repomix-output.ast-inner.xml");
-const finalOutput = resolve(repoRoot, "repomix-output.ast.xml");
-const headroomOutput = resolve(repoRoot, "repomix-output.headroom.xml");
-
-const repomixCli = resolve(repoRoot, "node_modules", "repomix", "bin", "repomix.cjs");
-const headroomOnly = process.argv.includes("--headroom-only");
-
-if (!headroomOnly) {
-  execFileSync(
-    process.execPath,
-    [
-      repomixCli,
-      "--config",
-      "repomix.config.json",
-      "--compress",
-      "--output",
-      innerOutput,
-      ".",
-    ],
+const DEFAULT_HEADROOM_PORT = 8797;
+const DEFAULT_HEADROOM_BASE_URL = `http://127.0.0.1:${DEFAULT_HEADROOM_PORT}`;
+const DEFAULT_TOKEN_BUDGET = 80_000;
+
+export async function buildRepositoryContextBundle(options = {}) {
+  const {
+    configPath = "repomix.config.json",
+    targetPath = ".",
+    headroomOnly = false,
+    fullOnly = false,
+  } = options;
+
+  const innerOutput = resolve(repoRoot, "repomix-output.ast-inner.xml");
+  const llmOutput = resolve(repoRoot, "repomix-output.xml");
+  const astOutput = resolve(repoRoot, "repomix-output.ast.xml");
+  const headroomOutput = resolve(repoRoot, "repomix-output.headroom.xml");
+  const fullOutput = resolve(repoRoot, "repomix-output.full.xml");
+
+  const repomixCli = resolve(repoRoot, "node_modules", "repomix", "bin", "repomix.cjs");
+  const headroomBaseUrl = (process.env.HEADROOM_BASE_URL || DEFAULT_HEADROOM_BASE_URL).replace(/\/$/, "");
+
+  if (fullOnly) {
+    execFileSync(
+      process.execPath,
+      [repomixCli, "--config", configPath, "--output", fullOutput, targetPath],
+      { cwd: repoRoot, stdio: "inherit" },
+    );
+    console.log(`Full (uncompressed) context written to ${fullOutput}`);
+    return { llmOutput: fullOutput, compression: "none", headroomActuallyCompressed: false };
+  }
+
+  if (!headroomOnly) {
+    execFileSync(
+      process.execPath,
+      [
+        repomixCli,
+        "--config",
+        configPath,
+        "--compress",
+        "--output",
+        innerOutput,
+        targetPath,
+      ],
+      { cwd: repoRoot, stdio: "inherit" },
+    );
+  }
+
+  const repomixSource = headroomOnly ? astOutput : innerOutput;
+  const compressedRepomixXml = readFileSync(repomixSource, "utf8")
+    .replace(/^\uFEFF/, "")
+    .replace(/^<\?xml[^>]*>\s*/u, "")
```

## `src/app/api/spiritflix/admin/smart/analysis/route.ts`
- exists: True
- diff stat: `.../api/spiritflix/admin/smart/analysis/route.ts   | 72 ++++++++++++++++++++--
 1 file changed, 68 insertions(+), 4 deletions(-)`

```diff
diff --git a/src/app/api/spiritflix/admin/smart/analysis/route.ts b/src/app/api/spiritflix/admin/smart/analysis/route.ts
index 7669e530..3fe9cb55 100644
--- a/src/app/api/spiritflix/admin/smart/analysis/route.ts
+++ b/src/app/api/spiritflix/admin/smart/analysis/route.ts
@@ -7,8 +7,19 @@ import {
   assertSmartVideoPathCandidate,
+  buildSmartRenamePreviewDraft,
   getSmartAnalysisPath,
   isSpiritFlixSmartVideoExtension,
+  projectApprovedSmartMetadata,
   readSmartAnalysis,
   type SpiritFlixSmartAnalysis,
+  writeApprovedSmartMetadataSidecar,
 } from "@/lib/spiritflix/admin/smart";
-import { markSpiritFlixSmartAnalysisReviewed, runSpiritFlixSmartReviewPipeline } from "@/lib/spiritflix/admin/smart/review";
+import { markSpiritFlixSmartAnalysisReviewed, runSpiritFlixSmartReviewPipeline, saveSpiritFlixSmartAnalysisReview } from "@/lib/spiritflix/admin/smart/review";
+import { assertSpiritFlixSmartReviewPayload } from "@/lib/spiritflix/admin/smart/review-metadata";
+
+const FORBIDDEN_EXECUTE_ACTIONS = new Set([
+  "applyRename",
+  "applyMove",
+  "executeRename",
+  "executeMove",
+]);

@@ -67,3 +78,5 @@ function jsonError(error: unknown, fallbackStatus = 500) {
   const message = error instanceof Error ? error.message : "Smart analysis request failed.";
-  const status = /only available|folder|video files/i.test(message) ? 400 : fallbackStatus;
+  const status = /only available|folder|video files|unknown field|known tag|review|overlap|must be|not in suggestedTags|too large/i.test(message)
+    ? 400
+    : fallbackStatus;
   return NextResponse.json({ error: message }, { status });
@@ -88,5 +101,5 @@ export async function GET(request: NextRequest) {
 export async function POST(request: NextRequest) {
-  let body: { path?: string; action?: string };
+  let body: { path?: string; action?: string; review?: unknown };
   try {
-    body = (await request.json()) as { path?: string; action?: string };
+    body = (await request.json()) as { path?: string; action?: string; review?: unknown };
   } catch {
@@ -118,2 +131,10 @@ export async function POST(request: NextRequest) {

+    // S6: reject all execute actions outright
+    if (FORBIDDEN_EXECUTE_ACTIONS.has(action)) {
+      return NextResponse.json(
+        { error: `${action} is not available in smart tagging. File mutations require Level 2 preview → confirm.` },
+        { status: 400 },
+      );
+    }
+
     let analysis: SpiritFlixSmartAnalysis;
@@ -121,4 +142,47 @@ export async function POST(request: NextRequest) {
       analysis = await markSpiritFlixSmartAnalysisReviewed(realPath, { mediaRoot });
+    } else if (action === "saveReview") {
+      const review = assertSpiritFlixSmartReviewPayload(
+        body.review ?? { approvedTagIds: [], rejectedTagIds: [] },
+      );
+      analysis = await saveSpiritFlixSmartAnalysisReview(realPath, review, { mediaRoot });
     } else if (action === "analyze") {
       analysis = await runSpiritFlixSmartReviewPipeline(realPath, { mediaRoot });
+    } else if (action === "exportMetadata") {
+      // S6: export approved metadata to admin metadata sidecar only
+      const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
+      const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
+      if (!loaded) {
+        return NextResponse.json({ error: "No smart analysis found for this video. Run analyze first." }, { status: 400 });
+      }
+      if (!loaded.reviewedMetadata || loaded.reviewedMetadata.reviewStatus === "unreviewed") {
+        return NextResponse.json({ error: "Analysis must be reviewed before exporting metadata." }, { status: 400 });
+      }
+      const result = await writeApprovedSmartMetadataSidecar(loaded, { mediaRoot });
+      const projection = projectApprovedSmartMetadata(loaded);
+      return NextResponse.json({
+        metadataPath: result.path,
+        metadata: projection,
+      }, { headers: { "Cache-Control": "no-store" } });
+    } else if (action === "prepareRenamePreview") {
+      // S6: build rename preview draft — no execute, no Level 2 call
+      const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
+      const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
```

## `src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx`
- exists: True
- diff stat: `.../admin/SpiritFlixSmartReviewPanel.tsx           | 386 +++++++++++++++++++--
 1 file changed, 363 insertions(+), 23 deletions(-)`

```diff
diff --git a/src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx b/src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
index bcda5ac2..e386820f 100644
--- a/src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
+++ b/src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
@@ -2,6 +2,7 @@

-import { useCallback, useEffect, useState } from "react";
+import { useCallback, useEffect, useMemo, useState } from "react";
 import { createPortal } from "react-dom";
 import { Sparkles, X } from "lucide-react";
-import type { SpiritFlixSmartAnalysis } from "@/lib/spiritflix/admin/smart";
+import type { SpiritFlixSmartAnalysis, SpiritFlixSmartReviewInput } from "@/lib/spiritflix/admin/smart/types";
+import { buildEmptyReviewDraft, countReviewTagStates, tagReviewState } from "@/lib/spiritflix/admin/smart/review-metadata";
 import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
@@ -20,2 +21,30 @@ interface SmartAnalysisResponse {

+interface ExportMetadataResponse {
+  metadataPath?: string;
+  metadata?: {
+    sourcePath: string;
+    displayTitle?: string;
+    filenameSuggestion?: string;
+    category?: string;
+    collections: string[];
+    approvedTags: Array<{ id: string; label: string; group: string; confidence: number }>;
+    rejectedTagIds: string[];
+    reviewStatus: string;
+    reviewedAt?: string;
+    notes?: string;
+  };
+  error?: string;
+}
+
+interface PrepareRenameResponse {
+  renamePreview?: {
+    sourcePath: string;
+    suggestedName: string;
+    targetPath: string;
+    warnings: string[];
+    readyForLevel2Preview: boolean;
+  };
+  error?: string;
+}
+
 function formatConfidence(value: number): string {
@@ -24,2 +53,22 @@ function formatConfidence(value: number): string {

+function formatReviewStatus(status: string | undefined): string {
+  switch (status) {
+    case "partially_reviewed":
+      return "Partially reviewed";
+    case "reviewed":
+      return "Reviewed";
+    case "rejected":
+      return "Rejected";
+    default:
+      return "Unreviewed";
+  }
+}
+
+function collectionsToInput(value: string): string[] {
+  return value
+    .split(",")
+    .map((entry) => entry.trim())
+    .filter(Boolean);
+}
+
 export function SpiritFlixSmartReviewPanel({ item, open, onClose }: SpiritFlixSmartReviewPanelProps) {
@@ -27,2 +76,12 @@ export function SpiritFlixSmartReviewPanel({ item, open, onClose }: SpiritFlixSm
   const [sidecarPath, setSidecarPath] = useState<string | null>(null);
+  const [draft, setDraft] = useState<SpiritFlixSmartReviewInput>({
+    approvedTagIds: [],
+    rejectedTagIds: [],
+    editedDisplayTitle: "",
+    editedFilenameSuggestion: "",
+    editedCategory: "",
+    editedCollections: [],
+    notes: "",
+  });
+  const [collectionsInput, setCollectionsInput] = useState("");
```

## `src/styles/spiritflix.css`
- exists: True
- diff stat: `src/styles/spiritflix.css | 99 +++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 99 insertions(+)`

```diff
diff --git a/src/styles/spiritflix.css b/src/styles/spiritflix.css
index 68873364..f9072be4 100644
--- a/src/styles/spiritflix.css
+++ b/src/styles/spiritflix.css
@@ -3812,2 +3812,101 @@

+.spiritflix-smart-review__boundary {
+  margin: 0 0 0.75rem;
+  padding: 0.55rem 0.65rem;
+  border-radius: 0.45rem;
+  background: rgb(14 116 144 / 18%);
+  color: #bae6fd;
+  font-size: 0.8rem;
+  line-height: 1.4;
+}
+
+.spiritflix-smart-review__field {
+  display: grid;
+  gap: 0.3rem;
+  margin-bottom: 0.65rem;
+}
+
+.spiritflix-smart-review__field span {
+  color: #cbd5e1;
+  font-size: 0.78rem;
+  font-weight: 650;
+}
+
+.spiritflix-smart-review__field input,
+.spiritflix-smart-review__field textarea {
+  width: 100%;
+  border: 1px solid rgb(148 163 184 / 22%);
+  border-radius: 0.4rem;
+  background: rgb(15 23 42 / 75%);
+  color: #f8fafc;
+  padding: 0.45rem 0.55rem;
+  font: inherit;
+}
+
+.spiritflix-smart-review__field small {
+  color: #fbbf24;
+  font-size: 0.72rem;
+}
+
+/* ── S6 approved metadata + rename preview ──────────────────────────── */
+.spiritflix-smart-review__section--approved {
+  border-color: #22c55e;
+}
+
+.spiritflix-smart-review__section--export-result {
+  border-color: #3b82f6;
+}
+
+.spiritflix-smart-review__section--rename-preview {
+  border-color: #a855f7;
+}
+
+.spiritflix-smart-review__section--actions .spiritflix-smart-review__action-buttons {
+  display: flex;
+  gap: 0.5rem;
+  flex-wrap: wrap;
+  margin-top: 0.5rem;
+}
+
+.spiritflix-smart-review__warning {
+  color: #fbbf24;
+  font-size: 0.72rem;
+  margin: 0;
+}
+
+.spiritflix-smart-tag-pill-wrap {
+  display: grid;
+  gap: 0.25rem;
+}
+
+.spiritflix-smart-tag-pill-wrap.is-approved .spiritflix-smart-tag-pill {
+  border-color: rgb(74 222 128 / 45%);
+  background: rgb(20 83 45 / 35%);
+}
+
```

## `scripts/media/face_organizer.py`
- exists: True
- diff stat: `scripts/media/face_organizer.py | 330 +++++++++++++++++++++++++++++++++-------
 1 file changed, 278 insertions(+), 52 deletions(-)`

```diff
diff --git a/scripts/media/face_organizer.py b/scripts/media/face_organizer.py
index eedda1b2..1fe76447 100644
--- a/scripts/media/face_organizer.py
+++ b/scripts/media/face_organizer.py
@@ -22,2 +22,3 @@ import base64
 import dataclasses
+import hashlib
 import html
@@ -88,2 +89,4 @@ VIDEO_EXTENSIONS = {
 EXCLUDED_SCAN_DIRS = {".face-review", "models", "unknown", "backups", "review_exports", "known_performers"}
+# Model-folder and unknown-folder uploads still need human verification before trust.
+VERIFICATION_QUEUE_EXCLUDED_DIRS = EXCLUDED_SCAN_DIRS - {"unknown", "models"}
 GALLERY_DIR_NAME = "model_gallery"
@@ -2352,3 +2355,2 @@ def find_verification_queue_videos(source_dir: Path, recursive: bool) -> list[Pa
     pattern = "**/*" if recursive else "*"
-    excluded_dirs = EXCLUDED_SCAN_DIRS - {"unknown"}
     videos = [
@@ -2358,3 +2360,3 @@ def find_verification_queue_videos(source_dir: Path, recursive: bool) -> list[Pa
         and path.suffix.lower() in VIDEO_EXTENSIONS
-        and not any(part in excluded_dirs for part in path.relative_to(source_dir).parts[:-1])
+        and not any(part in VERIFICATION_QUEUE_EXCLUDED_DIRS for part in path.relative_to(source_dir).parts[:-1])
     ]
@@ -2746,3 +2748,34 @@ def scan(config: OrganizerConfig) -> list[dict[str, Any]]:

-def scan_single_video(config: OrganizerConfig, video_path: Path) -> dict[str, Any]:
+def scan_recent_unscanned_videos(config: OrganizerConfig, *, limit: int = 12, max_age_hours: int = 72) -> list[str]:
+    """Face-scan freshly uploaded library files that never received a sidecar."""
+    if limit <= 0:
+        return []
+    cutoff = time.time() - max(1, int(max_age_hours)) * 3600
+    scanned: list[str] = []
+    candidates: list[tuple[float, Path]] = []
+    for video_path in find_verification_queue_videos(config.source_dir, config.recursive):
+        if meta_path_for(video_path).exists():
+            continue
+        try:
+            mtime = float(video_path.stat().st_mtime)
+        except Exception:
+            continue
+        if mtime < cutoff:
+            continue
+        candidates.append((mtime, video_path))
+    for _, video_path in sorted(candidates, key=lambda item: item[0], reverse=True):
+        try:
+            scan_single_video(config, video_path, refresh_pages=False)
+            scanned.append(str(video_path))
+        except Exception as exc:
+            logging.warning("Failed auto-scan for recent upload %s: %s", video_path, exc)
+        if len(scanned) >= limit:
+            break
+    if scanned:
+        logging.info("Auto-scanned %s recent upload(s) without face sidecars", len(scanned))
+        refresh_organizer_pages(config, refresh_stale_enrollment=True, include_verification_report=True, scan_recent_uploads=False)
+    return scanned
+
+
+def scan_single_video(config: OrganizerConfig, video_path: Path, *, refresh_pages: bool = True) -> dict[str, Any]:
     if not video_path.exists() or not video_path.is_file() or video_path.suffix.lower() not in VIDEO_EXTENSIONS:
@@ -2759,2 +2792,4 @@ def scan_single_video(config: OrganizerConfig, video_path: Path) -> dict[str, An
             write_nfo(video_path, meta["performers"])
+        if refresh_pages:
+            refresh_organizer_pages(config, refresh_stale_enrollment=True, scan_recent_uploads=False)
     else:
@@ -7765,2 +7800,48 @@ def unscanned_unknown_record(video_path: Path, config: OrganizerConfig) -> dict[

+def verification_attention_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
+    return [
+        record
+        for record in records
+        if record.get("verification_needed") or record_has_unknown_model(record)
+    ]
+
+
+def verification_queue_fingerprint_from_attention(attention: list[dict[str, Any]]) -> str:
+    parts: list[str] = []
+    for record in sorted(
+        attention,
+        key=lambda item: str(item.get("_resolved_video_path") or item.get("video_path") or item.get("path") or ""),
+    ):
+        path = str(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")
```

## `docs/media/spiritflix-smart-tagging-rename-plan.md`
- exists: True
- diff stat: `docs/media/spiritflix-smart-tagging-rename-plan.md | 14 ++++++++++++++
 1 file changed, 14 insertions(+)`

```diff
diff --git a/docs/media/spiritflix-smart-tagging-rename-plan.md b/docs/media/spiritflix-smart-tagging-rename-plan.md
index 9578d66a..1d4bce5e 100644
--- a/docs/media/spiritflix-smart-tagging-rename-plan.md
+++ b/docs/media/spiritflix-smart-tagging-rename-plan.md
@@ -927,2 +927,16 @@ Video card/context menus expose **Smart tags**. Panel reads sidecars via GET; ex

+### S5 implementation note (2026-06-16)
+
+S5 adds metadata-only approve/edit/reject inside the Smart tags panel:
+
+```text
+src/lib/spiritflix/admin/smart/review-metadata.ts
+src/lib/spiritflix/admin/smart/types.ts              — reviewedMetadata on analysis sidecar
+src/app/api/spiritflix/admin/smart/analysis/route.ts — action: saveReview
+src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
+src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
+```
+
+`saveReview` stores `reviewedMetadata` (approved/rejected tag ids, edited title/filename/category/collections, notes) in analysis sidecars only. No apply rename/move. No Level 2 calls.
+
 ## Environment notes
```

## Generated / Large Artifact Summary

- `scripts/media/face_enrolled_performers.html`: 73119419 bytes, mtime 2026-06-17T22:12:32.519792, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_enrolled_performers.json`: 2008426 bytes, mtime 2026-06-17T22:12:33.293799, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_enrollment_queue.html`: 12587901 bytes, mtime 2026-06-17T22:13:16.849189, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_enrollment_queue.json`: 174857 bytes, mtime 2026-06-17T22:13:16.910189, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_gallery.html`: 502036 bytes, mtime 2026-06-17T22:13:15.393176, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_gallery.json`: 1317932 bytes, mtime 2026-06-17T22:13:15.413176, bucket H; looks generated/evidence by path and extension.
- `scripts/media/face_verification_full_audit.html`: 187979891 bytes, mtime 2026-06-16T22:51:03.843267, bucket H; looks generated/evidence by path and extension.
- `scripts/media/known_db_audit.html`: 15017 bytes, mtime 2026-06-17T22:13:15.428176, bucket H; looks generated/evidence by path and extension.
- `scripts/media/known_db_audit.json`: 3074 bytes, mtime 2026-06-17T22:13:15.428176, bucket H; looks generated/evidence by path and extension.
- `scripts/media/manual_crop.html`: 18308 bytes, mtime 2026-06-17T22:13:16.957190, bucket H; looks generated/evidence by path and extension.
- `scripts/media/model_index.json`: 26577 bytes, mtime 2026-06-16T23:17:38.083561, bucket H; looks generated/evidence by path and extension.
- `scripts/media/performer_verification.json`: 386957 bytes, mtime 2026-06-16T23:17:38.081561, bucket H; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/00-git-status.txt`: 2545 bytes, mtime 2026-06-17T21:44:16.634255, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/00-preflight.md`: 9997 bytes, mtime 2026-06-17T21:44:16.634255, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/00-system-baseline.txt`: 6910 bytes, mtime 2026-06-17T21:44:16.635255, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/10-repo-inventory.md`: 19475 bytes, mtime 2026-06-17T21:53:52.326177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/11-bloat-map.json`: 31572 bytes, mtime 2026-06-17T21:46:50.517326, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md`: 23880 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md`: 3279 bytes, mtime 2026-06-17T21:53:52.327177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/14-gitignore-and-repomix-findings.md`: 53041 bytes, mtime 2026-06-17T21:53:52.327177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/20-source-of-truth-review.md`: 185005 bytes, mtime 2026-06-17T21:53:52.327177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/30-model-storage-audit.md`: 4399 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/40-dell-stability-audit.md`: 153805 bytes, mtime 2026-06-17T21:55:14.873035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/41-crash-signals.json`: 571 bytes, mtime 2026-06-17T21:52:45.427465, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/50-runtime-health-audit.md`: 25559 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/60-watcher-existing-state.md`: 280847 bytes, mtime 2026-06-17T21:53:52.331177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/61-watcher-design.md`: 4145 bytes, mtime 2026-06-17T21:53:52.332177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/62-approval-needed-next-actions.md`: 812 bytes, mtime 2026-06-17T21:53:52.332177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md`: 1341 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/index.md`: 811 bytes, mtime 2026-06-17T21:53:52.332177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md`: 1686 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_date_is.txt`: 45 bytes, mtime 2026-06-17T21:44:15.781243, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_df_h.txt`: 514 bytes, mtime 2026-06-17T21:44:15.968246, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_free_h.txt`: 225 bytes, mtime 2026-06-17T21:44:16.068247, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_head.txt`: 70 bytes, mtime 2026-06-17T21:44:15.872244, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_status.txt`: 2608 bytes, mtime 2026-06-17T21:44:15.850244, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_toplevel.txt`: 62 bytes, mtime 2026-06-17T21:44:15.864244, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_worktree.txt`: 69 bytes, mtime 2026-06-17T21:44:15.858244, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_hostname.txt`: 33 bytes, mtime 2026-06-17T21:44:15.766243, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_last_x_head.txt`: 5881 bytes, mtime 2026-06-17T21:44:16.634255, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_pwd.txt`: 36 bytes, mtime 2026-06-17T21:44:15.752243, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_uptime.txt`: 80 bytes, mtime 2026-06-17T21:44:16.107248, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_who_b.txt`: 64 bytes, mtime 2026-06-17T21:44:16.118248, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_artifact_names.txt`: 381918 bytes, mtime 2026-06-17T21:46:49.959319, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_du_depth2.txt`: 2209 bytes, mtime 2026-06-17T21:46:48.227296, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_count.txt`: 63 bytes, mtime 2026-06-17T21:46:48.327298, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_groups.txt`: 3807 bytes, mtime 2026-06-17T21:46:48.459299, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_extension_counts.txt`: 1286 bytes, mtime 2026-06-17T21:46:40.806201, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_file_count.txt`: 40 bytes, mtime 2026-06-17T21:46:38.210168, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_git_ls_files.txt`: 1119033 bytes, mtime 2026-06-17T21:46:50.491325, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_top_level_counts.txt`: 8388 bytes, mtime 2026-06-17T21:46:39.570185, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_cleanup_scripts.txt`: 34214 bytes, mtime 2026-06-17T21:46:50.373324, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_git_tracked_top.txt`: 1361 bytes, mtime 2026-06-17T21:46:50.408324, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_gitignore.txt`: 17185 bytes, mtime 2026-06-17T21:46:49.970319, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_untracked_top.txt`: 175 bytes, mtime 2026-06-17T21:46:50.477325, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_fail_signals.txt`: 37478 bytes, mtime 2026-06-17T21:46:51.974344, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_latest_evidence.txt`: 25612 bytes, mtime 2026-06-17T21:46:51.988345, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_ollama_model_paths.txt`: 34806 bytes, mtime 2026-06-17T21:46:51.908344, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_watcher_monitor.txt`: 86945 bytes, mtime 2026-06-17T21:46:51.957344, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_df_root_8tb.txt`: 185 bytes, mtime 2026-06-17T21:46:51.995345, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_8tb_models.txt`: 274 bytes, mtime 2026-06-17T21:46:52.402350, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_usr_ollama.txt`: 125 bytes, mtime 2026-06-17T21:46:52.164347, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_lsblk_f.txt`: 787 bytes, mtime 2026-06-17T21:46:52.005345, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_mount_8tb.txt`: 227 bytes, mtime 2026-06-17T21:46:52.013345, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ollama_list.txt`: 927 bytes, mtime 2026-06-17T21:47:31.500843, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ps_ollama.txt`: 141 bytes, mtime 2026-06-17T21:47:31.533844, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_models.txt`: 100 bytes, mtime 2026-06-17T21:46:52.146347, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_ollama.txt`: 86 bytes, mtime 2026-06-17T21:46:52.126346, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_read.txt`: 130 bytes, mtime 2026-06-17T21:47:32.451855, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_write.txt`: 131 bytes, mtime 2026-06-17T21:47:32.478855, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_cat_ollama.txt`: 589 bytes, mtime 2026-06-17T21:47:16.336653, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_show_ollama.txt`: 491 bytes, mtime 2026-06-17T21:47:16.359653, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_status_ollama.txt`: 2447 bytes, mtime 2026-06-17T21:47:16.281653, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_date_is.txt`: 45 bytes, mtime 2026-06-17T21:47:32.484856, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_dmesg_tail.txt`: 97 bytes, mtime 2026-06-17T21:51:02.477334, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_filtered_signals.txt`: 103723 bytes, mtime 2026-06-17T21:52:45.354464, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_boots.txt`: 2350 bytes, mtime 2026-06-17T21:50:25.708918, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_current_4h.txt`: 27182 bytes, mtime 2026-06-17T21:50:51.269207, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_prev_warn.txt`: 17222 bytes, mtime 2026-06-17T21:50:38.394062, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_yesterday_warn.txt`: 45344 bytes, mtime 2026-06-17T21:51:02.415333, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_current_4h.txt`: 110410 bytes, mtime 2026-06-17T21:51:02.010328, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_prev.txt`: 42241 bytes, mtime 2026-06-17T21:50:56.191263, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_last_x_120.txt`: 8807 bytes, mtime 2026-06-17T21:47:32.667858, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_uptime_s.txt`: 48 bytes, mtime 2026-06-17T21:47:32.492856, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_var_logs_tail.txt`: 67012 bytes, mtime 2026-06-17T21:51:23.767571, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_next_3000.txt`: 48 bytes, mtime 2026-06-17T21:53:51.772171, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_ollama_tags.txt`: 2878 bytes, mtime 2026-06-17T21:53:51.802171, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_health.txt`: 57 bytes, mtime 2026-06-17T21:53:51.722171, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_v1_health.txt`: 60 bytes, mtime 2026-06-17T21:53:51.748171, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_compose_ps.txt`: 48 bytes, mtime 2026-06-17T21:53:49.499147, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_ps.txt`: 815 bytes, mtime 2026-06-17T21:53:36.225007, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_listeners.txt`: 514 bytes, mtime 2026-06-17T21:52:46.697479, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_cpu.txt`: 5824 bytes, mtime 2026-06-17T21:52:47.956492, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_mem.txt`: 6197 bytes, mtime 2026-06-17T21:52:47.931492, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_failed.txt`: 458 bytes, mtime 2026-06-17T21:52:48.218495, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_status.txt`: 7486 bytes, mtime 2026-06-17T21:52:48.383497, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_tmux_ls.txt`: 97 bytes, mtime 2026-06-17T21:52:47.876491, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_crontab.txt`: 216 bytes, mtime 2026-06-17T21:53:52.143175, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_etc_systemd.txt`: 250 bytes, mtime 2026-06-17T21:53:52.161175, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_services.txt`: 1115 bytes, mtime 2026-06-17T21:53:51.936173, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_timers.txt`: 230 bytes, mtime 2026-06-17T21:53:52.040174, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_watch_files.txt`: 279258 bytes, mtime 2026-06-17T21:53:52.326177, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/summary.json`: 1181 bytes, mtime 2026-06-17T21:55:14.874035, bucket F; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json`: 126196 bytes, mtime 2026-06-17T11:49:09.910230, bucket D; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json`: 120845 bytes, mtime 2026-06-17T06:01:57.336162, bucket D; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json`: 126317 bytes, mtime 2026-06-17T11:46:46.164779, bucket D; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json`: 121759 bytes, mtime 2026-06-17T11:55:16.068536, bucket D; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json`: 125872 bytes, mtime 2026-06-17T11:43:51.131047, bucket D; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-audit-closeout.md`: 10210 bytes, mtime 2026-06-17T11:39:27.992646, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-battery-results.json`: 4845 bytes, mtime 2026-06-17T11:53:50.985394, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-claude-comparison.md`: 6579 bytes, mtime 2026-06-17T11:54:14.035707, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-latest-receipt.json`: 89449 bytes, mtime 2026-06-17T11:53:27.063064, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-preflight-probe.json`: 84995 bytes, mtime 2026-06-17T11:53:23.649017, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm01-calc-.json`: 22 bytes, mtime 2026-06-17T11:43:52.665061, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm01-calc/calculator.js`: 27 bytes, mtime 2026-06-17T11:40:14.178068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm02-api-status/status.ts`: 27 bytes, mtime 2026-06-17T11:40:14.178068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm03-html-browser/dashboard.html`: 33 bytes, mtime 2026-06-17T11:40:14.178068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm04-unsupported-tsx/modal.tsx`: 27 bytes, mtime 2026-06-17T11:40:14.178068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm05-synthetic-cheat/widget.html`: 33 bytes, mtime 2026-06-17T11:40:14.179068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm06-degraded-observe/helper.js`: 27 bytes, mtime 2026-06-17T11:40:14.179068, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/preflight/preflight-calc.js`: 67 bytes, mtime 2026-06-17T05:58:41.043408, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-latest-trace.json`: 131541 bytes, mtime 2026-06-17T11:53:27.858075, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-preflight-probe.json`: 124801 bytes, mtime 2026-06-17T11:53:23.663017, bucket C; looks generated/evidence by path and extension.
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm01-calc-.json`: 22 bytes, mtime 2026-06-17T11:43:52.682061, bucket C; looks generated/evidence by path and extension.
- `scripts/media/face_verification_report.json`: 183 bytes, mtime 2026-06-17T22:09:56.652390, bucket H; looks generated/evidence by path and extension.

## Answers

- Real active feature work: SpiritFlix S6 files in `src/app/api/spiritflix/admin`, `src/components/spiritflix/admin`, `src/lib/spiritflix/admin/smart`, `src/styles/spiritflix.css`, and `docs/media/spiritflix-smart-tagging-rename-plan.md`; media/face-organizer Python/test files under `scripts/media/` also look active.
- Generated files that should stay out of normal repomix: HTML/JSON media reports, Source Proxy evidence packets, FIP receipts, prior audit evidence, and this cleanup evidence packet.
- Safe to ignore from repomix later: evidence directories under `docs/evidence/**`, generated media report HTML/JSON, and bulky local report artifacts; exact patch is proposed but not applied.
- Must not touch until SpiritFlix S6 closeout: every Bucket A item.
- Must not touch until media/face organizer closeout: every Bucket B item plus generated media reports until Britton decides whether to ignore/archive them.
- Package/config changes needing focused review: `package.json`, `package-lock.json`, and `repomix.config.json`.
