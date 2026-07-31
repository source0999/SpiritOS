# Gate 2-J Remediation Autonomy Policy

## Operator-Granted Prospective Autonomy

Codex may create a prospective remediation sub-authorization only inside an
already operator-authorized parent gate or gate range. Every such record must
be hashed, committed before use, linked to its parent, and labeled
`EXECUTOR_REMEDIATION_SUB_AUTHORIZATION`.

The record must state its reason, exact scope, whether authority is narrowed,
unchanged, or expanded, and proof that authority did not expand. It must retain
all Proxy authority, containment, evidence, and terminal-truth invariants.

No remediation may add a model, provider, real-model permission,
repository-write permission, filesystem or network access, weaker containment,
cloud or paid service, JCode commit/push/merge/deploy/release authority,
benchmark or hidden-verifier access, or campaign advancement beyond the parent
stop boundary. Any such expansion requires a new operator authorization.

## Historical Classification

The five files created in `9f84fe55e` were prospective and remained inside the
original Batch 2 scope, but omitted `issued_by` and `issued_at_utc`. They are
therefore classified only by the new prospective record as
`RETROACTIVELY_CLASSIFIED_EXECUTOR_REMEDIATION_SUB_AUTHORIZATION`. This does
not rewrite their commits or misstate their original identity.
