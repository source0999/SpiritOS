# Gate 2-J.7 Clean Reproduction

status: `GREEN_WITH_REQUIRED_SERIAL_BUILD_PROFILE`

A fresh empty `HOME`, sanitized environment, and temporary evidence root replayed
the qualification checks without using the daily runtime:

| Check | Result |
|---|---|
| Baseline pack | `136 passed, 3 failed, 46 subtests` (the same characterized base defects) |
| 2-J focused suites | `62 passed in 2.09s` |
| Offline pinned build | passed with `CARGO_BUILD_JOBS=1` in `10m47s` |
| Reproduced binary | `d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc`; `jcode v0.58.51-dev (2444e7b6)` |
| Pinned audit checkout | clean |

The same fresh build using the default parallel setting aborted with
`free(): invalid next size (fast)` while compiling the provider graph. The
one-job build is therefore a required qualification containment/resource
profile, not an optional performance choice. No source, lockfile, provider,
model, task, or daily-runtime surface was changed.

Gate 2-J.7 is complete. The next gate is the committed diagnostic fixture seal;
the fixture remains unexecuted until the later controlled-comparison gate.
