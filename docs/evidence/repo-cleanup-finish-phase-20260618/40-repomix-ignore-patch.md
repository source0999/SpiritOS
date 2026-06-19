# Repomix ignore patch

## Diff

```diff
diff --git a/repomix.config.json b/repomix.config.json
index 7618c87e..4d9970d9 100755
--- a/repomix.config.json
+++ b/repomix.config.json
@@ -4,7 +4,7 @@
     "maxFileSize": 2000000
   },
   "output": {
-    "filePath": "repomix-output.xml",
+    "filePath": "repomix-output.full.xml",
     "style": "xml",
     "parsableStyle": true,
     "compress": true,
@@ -34,11 +34,26 @@
       "dist",
       "node_modules",
       ".git",
+      "docs/evidence/**/raw/**",
+      "docs/evidence/**/artifacts/**",
+      "docs/evidence/**/*receipt*.json",
+      "docs/evidence/**/*trace*.json",
+      "docs/evidence/**/*smoke*.json",
+      "docs/evidence/**/*trial*.json",
+      "docs/evidence/**/*debug*.json",
+      "docs/evidence/**/*tmp*.json",
       ".spirit-backups/**",
       "source_proxy/.spirit-backups/**",
       "source_proxy/data/**",
       "backend/searxng_data/**",
       "backend/volumes/**",
+      "**/node_modules/**",
+      "**/.next/**",
+      "**/dist/**",
+      "**/.venv/**",
+      "**/venv/**",
+      "**/__pycache__/**",
+      "**/*.pyc",
       "src/components/dashboard/demo-v4/**",
       "src/app/design-demo/**",
       "**/*demo*.*",
```
