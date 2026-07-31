# Gate 2-J.9G-S Pinned JCode Startup Diagnosis

## Verdict

PASS

## Binding

- Authorization: TERRA_HIGH_AUTHORIZED__GATE_2J_9G_S
- Authorization hash: 90b4548756c12bf8f0c9bd8b4d29999a73766af7e502eacdef858e6676a985a5
- Base commit: 89c8437e71a1714ee288f1ab90d834c3050e0702
- Pinned binary: 2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6

## Source and Runtime Findings

src/cli/dispatch.rs dispatches Command::Run to
commands::run_single_message_command; src/cli/commands.rs then creates an
in-process agent task rather than waiting for a terminal client. The first
controlled contained launch was traced with external strace, process-tree
inspection, and stdout/stderr capture. It reached provider-model cache lookup
and session initialization but never constructed a provider or opened a TCP
socket.

The decisive syscall was mkdir("/jcode-home/.jcode", 0777), which returned
EROFS (Read-only file system). The process then printed
Error: Read-only file system (os error 30) and exited 1. The prior wrapper's
listener wait had obscured this immediate child exit, producing the apparent
stall.

## Classification and Correction

Classification: JCODE_HOME_PERMISSION_FAILURE.

The selected Option B correction mounts a fresh tmpfs at /tmp, creates
/tmp/jcode-home, and explicitly sets HOME and JCODE_HOME to that ephemeral
writable directory. The preassembled executable root remains read-only,
network remains unshared, and no host JCode state is bound in.

A second bounded contained launch with no listener completed startup and
attempted the exact configured socket. It failed cleanly with ECONNREFUSED at
http://127.0.0.1:43123/v1/chat/completions, proving provider construction and
first socket connection are reached after the correction.

## Resource Correction

The prior values were /proc/status KiB mistakenly reported as bytes. Correct
conversion is RSS 276,824,064 bytes and virtual memory 515,899,392 bytes for
the reported values. The new sampler records byte units only; the failing
process exited before a valid peak sample, so no unsupported peak claim is
made for this launch.

## Counters and Integrity

- Diagnostic JCode launches: 2
- Fake requests: 0
- Real model requests: 0
- Direct Ollama requests: 0
- Repository writes by JCode: 0
- Benchmark changes: 0
- Daily-runtime changes: 0

The accepted next gate is 2-J.9G-B retry V2, which must prove the sealed fake
route using this corrected fresh home.
