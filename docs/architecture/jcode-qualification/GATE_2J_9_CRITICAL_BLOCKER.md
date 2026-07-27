# Gate 2-J.9 Critical Blocker: Controlled Comparison Authorization

status: `BLOCKED_OPERATOR_AUTHORIZATION_REQUIRED`

The sealed `jcode-diagnostic-20-20260727` fixture is intentionally unexecuted.
Gate 2-J.9 would start a model-backed controlled comparison, create provider
traffic, and obtain an observed actual-model receipt. The 2-J.8 seal explicitly
requires separate controlled-execution authorization before that happens.

No such authorization is present in the campaign authority records. Campaign 2
acceptance authorized the post-C2 qualification gates and preserved the disabled
adapter boundary; it did not authorize a JCode task, provider call, model call,
or fixture execution. The default executor remains unchanged and
`JCODE_EXECUTOR_ENABLED` remains disabled.

Required external decision: an operator must approve or reject a bounded
2-J.9 run packet identifying the exact sealed manifest digest, isolated
worktree/home/evidence roots, provider route, model, budgets, independent Proxy
checks, abort conditions, and result-retention policy. Until then Gates 2-J.9
and 2-J.10 cannot begin.
