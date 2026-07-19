# Benchmark secrecy design

The harness process owns the private benchmark store, seeds, hidden tests,
expected dispositions, oracle rules, and decoys. The independent oracle process
reads that store and immutable evidence only. The production coder process sees
only a task prompt, approved disposable fixture workspace, declared tools, and
the minimum context packet; it cannot mount, read, enumerate, or query the
private store or oracle state.

Enforce separate OS identities, mount namespaces, filesystem ACLs, separate
credentials, one-way evidence ingestion, and deny-by-default network/search
allowlists. Fixture worktrees are disposable and isolated from the evidence
store. Search roots and retrieval namespaces exclude private benchmark data;
this exclusion covers Mac Search, Scout, Obsidian, retained-context services,
OpenHands workspaces, LangGraph state, Agents SDK context, remote-worker mounts,
reviewer inputs, verifier inputs, and context-pack inputs. Reviewers/verifiers
receive task-local artifacts plus redacted evidence, never answer keys.

Before every run, a canary with synthetic private identifiers must demonstrate
that production-path search, filesystem enumeration, tool calls, worker mounts,
and context construction cannot retrieve them. A canary hit is a hard failure;
the task must not start. Production improvements may use generalized findings,
never task IDs, prompt hashes, benchmark paths, hidden-test names, seeds, or
expected results.
