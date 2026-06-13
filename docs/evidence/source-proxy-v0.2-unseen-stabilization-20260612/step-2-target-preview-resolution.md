# Step 2 Target/Preview Resolution

Verdict: GO

The resolver no longer assumes `workspace/index.html`. It prefers valid explicit preview evidence, then `index.html`, then a single HTML file, then a semantic prompt-slug match, and otherwise emits an ambiguous or missing reason code. Stale explicit remote paths fall back to generated workspace HTML and record `explicit_preview_path_invalid_fallback_used`.
