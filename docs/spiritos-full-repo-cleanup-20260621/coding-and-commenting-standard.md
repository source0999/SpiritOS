# Coding & Commenting Standard — F1–F10

Required code qualities for all cleanup edits. Reviewers (Codex/Britton) check
against this. Splits are by cohesion/responsibility, never by line count alone.

## Architecture
- **Thin routers:** API route handlers serialize/deserialize and delegate; they
  do not contain domain logic. (F5 target.)
- **Cohesive modules:** each module has one responsibility; cross-cutting
  concerns are explicit, not implicit.
- **Typed stable contracts:** public functions have typed signatures and stable
  input/output contracts (the compatibility contract freezes the observable ones).

## Correctness & safety
- **No duplicated truth calculations:** a fact is computed in one place.
- **No hidden import-time side effects:** imports must not start processes,
  open sockets, mutate global state, or call the network.
- **Bounded side effects:** I/O/process/network is explicit and localized.
- **Timeouts for network/process calls:** every external call has a timeout
  (F9 adapter contract makes this explicit).
- **No broad `except`/`pass`** without a documented safe reason. A bare
  `except: pass` must carry a comment explaining why it is safe and what is
  swallowed.

## Naming & docs
- **Descriptive names:** names say what, not how-implementation-detail.
- **Comments for intent, invariants, risk, safety, non-obvious tradeoffs** —
  not for restating syntax.
- **No syntax-restating comments** (e.g. `# increment i` above `i += 1`).
- **Short public-contract docstrings** on every public function/module.
- **Documented state transitions** (F6 engine: transitions, apply authority,
  recovery idempotence).
- **Documented anti-cheat purpose** on any detection/verification code (F2):
  what it catches and why it is independent.

## Refactor discipline
- **No split by line count alone.** A 7,971-line file is split into cohesive
  lanes/responsibilities, not arbitrary 1,500-line chunks.
- **Safe first patch:** pure extraction → compatibility import → parity proof →
  canonical switch → exact retirement only after proof.
- **Temporary compatibility adapters** are labeled, have parity tests, and carry
  a retirement/review condition. They never count as new capability.

## Comments required in this cleanup specifically
- Where a failure classification is emitted (F1): why this class, not another.
- Where a fallback is used (F8/F9): the primary path, the fallback, and the
  recorded `fallback_used` evidence.
- Where a benchmark-relevant path exists (F3/F4): that the path is generic and
  why it is not benchmark-keyed.
- Where a protected boundary is near (any stage): the path guard in effect.

## Review heuristics (for Codex)
- Could a module's responsibility be stated in one sentence? If not, split more.
- Is any `except` swallowing a failure that should be classified (F1)? Flag it.
- Is any positive verdict derivable without running the system? If yes, §C violation.
- Does any branch read like it exists to make a specific known case pass? §A violation.
