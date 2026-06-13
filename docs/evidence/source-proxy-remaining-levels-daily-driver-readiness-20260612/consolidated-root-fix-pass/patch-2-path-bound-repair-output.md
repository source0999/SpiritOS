# Patch 2: Path-Bound Repair Output Contract Hardening

Status: PASS_SUBCHECK

## Changed Files

- `source_proxy/decision/artifact_repair_loop.py`
- `source_proxy/decision/tool_action_executor.py`
- `source_proxy/tests/test_artifact_repair_loop.py`

## What Changed

- Repair attempts now accept model-authored path-bound `.html`, `.css`, and `.js` file blocks in the disposable workspace.
- Free-floating code remains rejected.
- Secret paths, protected paths, package files, path traversal, and real app/source paths are blocked.
- Repair results now preserve parse decisions, rejected repair transcripts, valid repaired targets, repaired file hashes, and a `bytes_written_match_model_authored_content` equality signal.
- Unsafe target receipts now keep the specific reason code, such as `protected_path` instead of flattening every unsafe target to `path_escape`.

## Accepted Repair Example

```text
<file path="index.html">
<!doctype html><html><head><link rel="stylesheet" href="styles.css"></head><body><button id="go">Add</button><output>5</output><script src="app.js"></script></body></html>
</file>
<file path="styles.css">
body { font-family: system-ui; }
</file>
<file path="app.js">
document.querySelector('#go').addEventListener('click',()=>document.querySelector('output').textContent='5');
</file>
```

Accepted result:

```json
{
  "status": "READY_FOR_RETEST",
  "repaired_files": ["app.js", "index.html", "styles.css"],
  "bytes_written_match_model_authored_content": true
}
```

## Rejected Repair Examples

```text
```html
<html><body>no path</body></html>
```
```

Rejected with `free_floating_code_no_path_action`.

```text
<file path=".env">TOKEN=bad</file>
<file path="package.json">{}</file>
<file path="src/app.html"><!doctype html></file>
<file path="../outside.html"><!doctype html></file>
```

Rejected with `protected_path`, `target_not_allowed`, or `path_escape`.

## Tests Run

```text
python -m pytest source_proxy/tests/test_artifact_repair_loop.py source_proxy/tests/test_coding_regression_pack.py -k "tool_action or repair or protected or backend_authored or fallback"
44 passed, 1 skipped, 89 deselected

python -m py_compile source_proxy/decision/tool_action_executor.py source_proxy/decision/artifact_repair_loop.py source_proxy/tests/test_artifact_repair_loop.py
PASS

git diff --check -- source_proxy/decision/tool_action_executor.py source_proxy/decision/artifact_repair_loop.py source_proxy/tests/test_artifact_repair_loop.py
PASS
```

`git diff --check` printed a line-ending warning for `source_proxy/decision/tool_action_executor.py`; no whitespace errors were reported.

## Remaining Risks

- This proves the local parser/executor/repair-loop contract. End-to-end improvement still depends on the model returning valid path-bound repair output and the browser retest passing.
- The one-attempt cap remains enforced; failed first repairs still stop for review.
