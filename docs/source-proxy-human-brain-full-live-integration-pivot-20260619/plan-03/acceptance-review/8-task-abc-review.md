# Task A/B/C Review

Task A: policy denial before mutation
- Task: `task_6ecf07847f44`
- Trace: `trace_6d3256350cd748f2`
- Final status: `policy_blocked`
- Verdict: NEEDS_FIX
- Reason: policy block is persisted, but no consumer event or latest consumer id was present.

Task B: interruption and recovery from persisted state
- Task: `task_b8e307901b22`
- Trace: `trace_10a21d27c6c14f5e`
- Final status: `worker_dispatched`
- Verdict: NEEDS_FIX
- Reason: recovery metadata is persisted, but no consumer event or latest consumer id was present.

Task C: verifier failure, repair, and reverify
- Task: `task_938dad74a7d9`
- Trace: `trace_31500112a69a42bf`
- Final status: `verified`
- Verdict: NEEDS_FIX
- Reason: repair and reverify are present, but the trace lacks an explicit failure event and lacks downstream consumer evidence.

Combined Task A/B/C verdict: NEEDS_FIX.
