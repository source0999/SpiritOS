SPIRITOS INTELLIGENCE OVERHAUL MASTER IMPLEMENTATION PLAN
ARPA STYLE

A = Analyze
R = Research / repo-aware constraints
P = Plan
A = Ask permission before each coding phase

Core rule:
Do not let Cursor implement the whole intelligence overhaul at once. This is a phased architecture upgrade. Each phase must preserve the current app, pass tests, and leave a rollback point before moving forward.

Primary goal:
Upgrade Hermes from a static chatbot into a dynamic SpiritOS intelligence layer with live context, shared memory options, safe tools, file awareness, guarded edits, and eventually allowlisted dev-command execution.

Non-negotiables:
- Do not delete existing model profiles early.
- Do not remove Oracle’s current behavior until memory rules are explicit.
- Do not add raw shell access.
- Do not give the model unrestricted file writes.
- Do not hardcode hardware facts unless they come from env/config.
- Every phase must preserve current chat, Oracle, TTS, STT, and web research behavior unless the phase explicitly changes it.
- Every phase must have tests or at least typecheck before moving on.

==================================================
PHASE 0: REPO CONTRACT AUDIT
==================================================

Goal:
Create a clear map of the current intelligence runtime before changing anything. This prevents Cursor from hallucinating architecture or deleting important behavior.

Exact files to inspect:
- src/lib/spirit/model-profiles.ts
- src/lib/spirit/model-runtime.ts
- src/app/api/spirit/route.ts
- src/hooks/useSpiritChatTransport.ts
- src/lib/oracle/oracle-voice-session.ts
- src/lib/chat/chat-db.ts
- src/components/spirit/ModelProfileSelector.tsx
- src/hooks/useSpiritModeRuntime.ts
- Any tests related to model runtime, model profiles, chat transport, Oracle, and API route

Files not to touch:
- Do not edit anything in this phase.
- Do not delete modes.
- Do not change Oracle persistence.
- Do not add tools.

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze the current SpiritOS intelligence runtime only. Do not write code yet.

Inspect these files:
- src/lib/spirit/model-profiles.ts
- src/lib/spirit/model-runtime.ts
- src/app/api/spirit/route.ts
- src/hooks/useSpiritChatTransport.ts
- src/lib/oracle/oracle-voice-session.ts
- src/lib/chat/chat-db.ts
- src/components/spirit/ModelProfileSelector.tsx
- src/hooks/useSpiritModeRuntime.ts
- related tests

Create a repo contract report that explains:
1. How profiles currently work
2. How buildModelRuntime builds the final system prompt
3. How /api/spirit/route.ts calls streamText
4. How chat persistence works
5. Why Oracle is currently ephemeral or non-persistent
6. Where web search is wired
7. What tests would break if profiles or transports were rewritten
8. What files must not be touched during Phase 1

R: Compare the current repo to the intelligence-overhaul goal:
- dynamic system state
- soft persona routing
- optional shared memory
- safe local tools
- guarded file edits
- allowlisted bash later

P: Propose a minimal Phase 1 implementation plan only.

A: Stop and ask for permission before writing code.”

Behavior preserved + tests to run:
- No behavior should change.
- Run:
  - npm run typecheck
  - npm test, if available
  - Or the closest existing test command

Rollback point:
- No rollback needed because no code changes should happen.

Success criteria:
- Cursor produces an accurate repo contract.
- Cursor identifies exact files for Phase 1.
- Cursor does not write code yet.

==================================================
PHASE 1: DYNAMIC SYSTEM STATE LAYER
==================================================

Goal:
Make Hermes aware of runtime context without deleting existing profiles. Add a [SYSTEM STATE] block that injects current time, surface, model hint, hardware profile, and available/unavailable capabilities.

Exact files to touch:
- src/lib/spirit/system-state.ts, new file
- src/lib/spirit/model-runtime.ts
- src/app/api/spirit/route.ts
- Tests for model-runtime or route behavior

Files not to touch:
- Do not delete src/lib/spirit/model-profiles.ts
- Do not edit ModelProfileSelector UI
- Do not edit Oracle persistence
- Do not edit chat-db
- Do not add tools yet
- Do not add bash
- Do not add file editing

Precise Cursor prompt:

“Work in ARPA mode.

A: Re-read the repo contract from Phase 0. Confirm how buildModelRuntime currently assembles the system prompt.

R: We are adding dynamic context without deleting existing profiles. This should make Hermes more self-aware while preserving all current behavior.

P: Implement Phase 1 only.

Task:
Create a typed dynamic system state module.

Files:
1. Add src/lib/spirit/system-state.ts
2. Update src/lib/spirit/model-runtime.ts
3. Update src/app/api/spirit/route.ts
4. Add or update tests related to model-runtime

Implementation requirements:
- Create buildSystemStateBlock(input)
- Input should include:
  - current time as ISO string
  - runtimeSurface: “chat” | “oracle”
  - modelHint or modelId if available
  - hardware profile from env/config or safe fallback
  - available capabilities
  - unavailable capabilities

Initial available capabilities:
- chat
- tts
- stt
- web_search_when_enabled

Initial unavailable capabilities:
- terminal_execution
- file_editing
- email_access
- calendar_access

Important:
- Do not hardcode exact hardware as truth unless it comes from env/config.
- Allow env vars like:
  - SPIRIT_HARDWARE_PROFILE
  - SPIRIT_PROJECT_PATH
  - SPIRIT_LOCAL_MODEL
- If env vars are missing, say “unknown” or “not configured.”
- Append [SYSTEM STATE] inside buildModelRuntime after surface instruction and before response budget/final answer contract, based on the existing order.
- Preserve all existing profile behavior.
- Preserve deep think behavior.
- Preserve web research behavior.
- Preserve Oracle surface behavior.
- Preserve source rules.
- Preserve response budget logic.

A: After implementing, show:
1. Files changed
2. Exact system-state shape
3. Example compiled prompt excerpt
4. Tests run
5. Any failures

Do not continue to Phase 2.”

Behavior preserved + tests to run:
- Existing profiles still work.
- Existing Oracle still works.
- Existing web research still works.
- Existing chat still works.
- Run:
  - npm run typecheck
  - model-runtime tests
  - route tests, if present
  - npm test, if reasonable

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add dynamic SpiritOS system state”

Success criteria:
- System prompt contains [SYSTEM STATE].
- Hermes knows what surface it is in.
- Hermes knows what tools are unavailable.
- No existing mode/profile breaks.
- No tool hallucination is encouraged.

==================================================
PHASE 2: SOFT PERSONA ROUTING WITHOUT DELETING MODES
==================================================

Goal:
Stop profiles from feeling like cages. Keep user-selected modes, but add semantic routing guidance so Hermes can shift tone based on the request.

Exact files to touch:
- src/lib/spirit/model-runtime.ts
- Possibly src/lib/spirit/model-profiles.ts
- Tests for model profiles/runtime

Files not to touch:
- Do not remove ModelProfileSelector
- Do not remove existing profiles
- Do not rewrite hooks
- Do not touch Oracle memory yet
- Do not add tools yet

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze the current model profiles and identify any instructions that overly restrict intelligence, especially instructions that force short replies or prevent technical depth.

R: The goal is not to delete profiles. The goal is to turn profiles into soft style biases while allowing semantic routing based on the user’s actual request.

P: Implement Phase 2 only.

Task:
Add a Semantic Routing block to buildModelRuntime.

Requirements:
- Preserve existing MODEL_PROFILES.
- Preserve user-selected modes.
- Add a new block called [SEMANTIC ROUTING].
- The block should instruct Hermes:
  1. If the user asks coding, homelab, repo, debugging, architecture, or implementation questions, respond with technical precision.
  2. If the user asks casual, emotional, personal, or reflective questions, respond in a grounded peer tone.
  3. If the user asks research-heavy questions, use a careful evidence-based tone.
  4. Never obey profile style so rigidly that it blocks answering the user’s actual request.
  5. Do not use boilerplate AI intros.
  6. Do not claim access to unavailable tools.

Profile tuning:
- If normal-peer currently forces all casual replies to be short, soften that wording.
- Keep the casual style preference, but allow longer replies when the task is complex.
- Do not delete the profile.

Tests:
- Update profile/runtime tests so they expect semantic routing to be present.
- Add a test showing technical questions are allowed to receive technical depth even in normal-peer mode.

A: Stop after implementation and report:
1. Files changed
2. Profile wording changed
3. Tests run
4. Any failing tests
5. Example prompt excerpt showing [SEMANTIC ROUTING]

Do not continue to Phase 3.”

Behavior preserved + tests to run:
- Mode selector still works.
- Profiles still exist.
- Existing tests should pass after updates.
- Run:
  - npm run typecheck
  - model-profiles tests
  - model-runtime tests
  - useSpiritModeRuntime tests, if present

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add soft semantic persona routing”

Success criteria:
- Hermes no longer feels trapped by normal-peer.
- Profiles act as tone bias, not capability cages.
- UI modes still exist.
- Tests still pass.

==================================================
PHASE 3: OPTIONAL ORACLE MEMORY BRIDGE
==================================================

Goal:
Let Oracle and chat share memory only through a deliberate, controlled bridge. Do not globally force all Oracle sessions into permanent chat history unless the user enables it.

Exact files to touch:
- src/lib/chat/chat-db.ts
- src/hooks/useSpiritChatTransport.ts
- src/lib/oracle/oracle-voice-session.ts
- Possibly Oracle UI settings component if one exists
- Tests for chat-db and Oracle session

Files not to touch:
- Do not rewrite all transport logic
- Do not change TTS/STT behavior
- Do not delete existing chat threads
- Do not force all Oracle transcripts into every chat by default

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze current chat Dexie persistence and Oracle voice persistence. Confirm Oracle currently does not persist like normal chat.

R: We need shared memory, but as a product-safe bridge. Oracle should be able to write compact memory events to a shared context thread without turning every voice session into messy permanent chat history.

P: Implement Phase 3 only.

Task:
Create an optional Oracle memory bridge.

Requirements:
1. In chat-db.ts, add support for a special system thread:
   - threadId: “oracle-global”
   - title: “Oracle Memory”
   - type or metadata: system/oracle
2. Add functions:
   - appendOracleMemoryEvent()
   - getRecentOracleMemoryEvents(limit)
   - clearOracleMemoryEvents()
3. Memory event shape should include:
   - id
   - timestamp
   - source: “oracle”
   - userTranscript
   - assistantSummary
   - optional full assistant text only if safe and not too large
4. Oracle should write a compact summary, not necessarily the full transcript.
5. Chat runtime should be able to optionally include recent Oracle memory events in context.
6. Default behavior:
   - If no setting exists, keep Oracle memory bridge disabled by default.
   - Or add an env/config flag:
     SPIRIT_ENABLE_ORACLE_MEMORY=true
7. The system prompt should clearly say whether Oracle memory is enabled or disabled.
8. Do not mix Oracle memory into all chats without a clear function boundary.

Tests:
- Add tests for appending Oracle memory.
- Add tests for retrieving recent Oracle memory.
- Add tests for disabled bridge behavior.
- Add tests that existing chat threads still work.

A: Stop after implementation and report:
1. Files changed
2. New Dexie schema changes
3. Whether migration is required
4. Tests run
5. How to enable/disable Oracle memory

Do not continue to Phase 4.”

Behavior preserved + tests to run:
- Existing chat history remains intact.
- Oracle still works if memory is disabled.
- No broken Dexie migrations.
- Run:
  - npm run typecheck
  - chat-db tests
  - Oracle session tests
  - transport tests

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add optional Oracle memory bridge”

Success criteria:
- Oracle can share memory when enabled.
- Oracle remains ephemeral when disabled.
- Chat can reference recent Oracle summaries.
- Dexie remains stable.

==================================================
PHASE 4: READ-ONLY LOCAL TOOLS
==================================================

Goal:
Give Hermes safe “eyes” before giving it “hands.” It should be able to inspect workspace files, list safe directories, read logs, and check system status.

Exact files to touch:
- src/lib/spirit/tools/tool-registry.ts, new
- src/lib/spirit/tools/workspace-tools.ts, new
- src/lib/spirit/tools/tool-safety.ts, new
- src/app/api/spirit/route.ts
- src/lib/spirit/system-state.ts
- Tests for tools and route

Files not to touch:
- Do not add edit tools yet
- Do not add bash yet
- Do not execute arbitrary commands
- Do not read .env
- Do not read secrets
- Do not read outside workspace

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze how /api/spirit/route.ts currently calls streamText and whether the installed AI SDK version supports tools with inputSchema and execute.

R: We are adding read-only local tools only. The purpose is to let Hermes inspect the project safely without hallucinating file contents.

P: Implement Phase 4 only.

Task:
Add a typed tool registry for read-only tools.

New files:
- src/lib/spirit/tools/tool-safety.ts
- src/lib/spirit/tools/workspace-tools.ts
- src/lib/spirit/tools/tool-registry.ts

Read-only tools:
1. list_workspace_files
   - input: relative directory path
   - output: list of files/folders
   - must stay inside SPIRIT_PROJECT_PATH or safe default workspace
   - block node_modules, .git, .next, dist, build, .env files

2. read_workspace_file
   - input: relative file path
   - output: file content
   - max file size limit
   - block .env, secrets, private keys, node_modules, .git, build artifacts

3. read_log_tail
   - input: relative log file path and line count
   - output: last N lines
   - same path restrictions

4. get_system_status
   - input: none
   - output: configured model, surface, project path configured or not, capabilities enabled

Safety:
- Use path.resolve and verify resolved path starts with the allowed workspace root.
- Never allow absolute paths from user input.
- Never allow traversal using ../
- Add blocked filename patterns.
- Add max output length.
- Return structured error objects, not thrown raw stack traces.

Route:
- Wire tools into streamText only when SPIRIT_ENABLE_LOCAL_TOOLS=true.
- Update system-state capabilities:
  - available: read_workspace_file, list_workspace_files, read_log_tail, get_system_status
  - unavailable: file_editing, terminal_execution, email_access, calendar_access

Tests:
- Path traversal blocked
- .env blocked
- node_modules blocked
- normal file read works
- disabled tools are not exposed
- route still works without tools

A: Stop after implementation and report:
1. Files changed
2. Tool list
3. Safety rules
4. Tests run
5. Any AI SDK compatibility issues

Do not continue to Phase 5.”

Behavior preserved + tests to run:
- Chat still works without tools.
- Tools only expose when enabled.
- No private files can be read.
- Run:
  - npm run typecheck
  - tool safety tests
  - route tests
  - npm test, if reasonable

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add safe read-only SpiritOS tools”

Success criteria:
- Hermes can inspect safe workspace files.
- Hermes no longer hallucinates file contents as often.
- Tools are disabled unless enabled.
- Secrets are blocked.

==================================================
PHASE 5: GUARDED FILE EDIT TOOLS
==================================================

Goal:
Allow Hermes to propose and apply file edits safely, but only with review, diff preview, and backups.

Exact files to touch:
- src/lib/spirit/tools/file-edit-tools.ts, new
- src/lib/spirit/tools/tool-registry.ts
- src/lib/spirit/tools/tool-safety.ts
- src/app/api/spirit/route.ts
- UI confirmation component or existing chat action UI
- Tests for file edit tools

Files not to touch:
- Do not add bash yet
- Do not allow editing .env
- Do not allow editing package-lock blindly
- Do not edit outside workspace
- Do not allow model to auto-apply destructive edits

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze the Phase 4 tool registry and safety helpers. Confirm read-only tools are stable before adding write tools.

R: File editing must be guarded. Hermes may draft edits, but user confirmation is required before applying.

P: Implement Phase 5 only.

Task:
Add guarded file edit tools.

New file:
- src/lib/spirit/tools/file-edit-tools.ts

Tools:
1. propose_file_edit
   - input:
     - relativeFilePath
     - newContent
     - reason
   - output:
     - diff preview
     - safety verdict
     - confirmationRequired: true
   - does not write the file

2. apply_confirmed_file_edit
   - input:
     - relativeFilePath
     - newContent
     - confirmationToken or confirmation id
   - output:
     - backup path
     - write status
   - only works after user confirmation

Safety:
- Same path restrictions from Phase 4
- Block .env, secrets, .git, node_modules, build artifacts
- Max file size limit
- Create backup before writing
- Generate unified diff preview before write
- Refuse binary files
- Refuse hidden sensitive files
- Refuse if confirmation is missing

UI:
- Add a basic confirmation flow.
- The model can propose edits.
- The user must approve before apply_confirmed_file_edit runs.
- Keep this minimal and functional.

Route:
- Expose write tools only when:
  SPIRIT_ENABLE_FILE_EDIT_TOOLS=true
- Update system-state capabilities accordingly.
- Clearly mark file editing unavailable when disabled.

Tests:
- propose edit does not write
- apply without confirmation fails
- apply with confirmation writes and creates backup
- blocked files cannot be edited
- traversal blocked
- binary file blocked

A: Stop after implementation and report:
1. Files changed
2. Confirmation flow
3. Backup behavior
4. Tests run
5. Known limitations

Do not continue to Phase 6.”

Behavior preserved + tests to run:
- Read-only tools still work.
- Chat still works without write tools enabled.
- No file is edited without confirmation.
- Run:
  - npm run typecheck
  - file-edit tool tests
  - tool safety tests
  - route tests

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add guarded SpiritOS file edit tools”

Success criteria:
- Hermes can propose edits.
- User sees diff before applying.
- Confirmed edits create backups.
- Unsafe paths are blocked.

==================================================
PHASE 6: ALLOWLISTED DEV COMMAND TOOLS
==================================================

Goal:
Give Hermes limited terminal-like power for safe development commands only. No raw shell. No arbitrary child_process.exec.

Exact files to touch:
- src/lib/spirit/tools/dev-command-tools.ts, new
- src/lib/spirit/tools/tool-registry.ts
- src/lib/spirit/tools/tool-safety.ts
- src/app/api/spirit/route.ts
- UI confirmation flow, if needed
- Tests for dev command tools

Files not to touch:
- Do not add execute_bash
- Do not allow arbitrary shell strings
- Do not allow rm, curl, wget, sudo, chmod, ssh, scp, env, cat .env, etc.
- Do not allow commands outside allowlist

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze Phase 4 and 5 tools. Confirm tool safety helpers are reusable.

R: We are not adding raw bash. We are adding allowlisted dev commands only.

P: Implement Phase 6 only.

Task:
Add allowlisted dev command tools.

New file:
- src/lib/spirit/tools/dev-command-tools.ts

Tool:
run_dev_command

Input:
- commandId only, not raw command string

Allowed commandIds:
- git_status
- git_diff
- npm_typecheck
- npm_test
- npm_lint
- npm_build, optional and confirmation-required

Implementation:
- Map commandId to a fixed command array.
- Use child_process.spawn, not raw exec.
- cwd must be SPIRIT_PROJECT_PATH.
- Timeout required.
- Max output length required.
- Capture stdout and stderr.
- Return structured output.
- No shell interpolation.
- No arbitrary arguments at first.
- Commands that may take longer or alter state require confirmation.

Safety:
- Tool disabled unless SPIRIT_ENABLE_DEV_COMMAND_TOOLS=true
- No raw shell command accepted
- No user-provided command strings
- No environment dumping
- No network commands

Tests:
- allowed command maps correctly
- unknown commandId rejected
- timeout works
- output cap works
- disabled tool unavailable
- no raw command accepted

A: Stop after implementation and report:
1. Files changed
2. Allowlisted command IDs
3. Safety limits
4. Tests run
5. Any failures

Do not continue to Phase 7.”

Behavior preserved + tests to run:
- File tools remain guarded.
- No arbitrary shell exists.
- Run:
  - npm run typecheck
  - dev-command tests
  - route tests
  - npm test, if reasonable

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add allowlisted SpiritOS dev command tools”

Success criteria:
- Hermes can run safe dev checks.
- Hermes cannot run arbitrary shell.
- Output returns cleanly into chat.
- Dangerous commands are impossible by design.

==================================================
PHASE 7: TOOL ACTIVITY UI + TELEMETRY
==================================================

Goal:
Make Hermes’ actions visible. The user should see when Hermes reads a file, proposes an edit, applies an edit, or runs a dev command.

Exact files to touch:
- Chat message rendering components
- Tool activity component, new if needed
- src/hooks/useSpiritChatTransport.ts
- API route streaming/tool result handling
- Existing diagnostics panel, optional

Files not to touch:
- Do not redesign the whole UI
- Do not change Oracle visual design
- Do not rewrite chat transport unless needed
- Do not add new capabilities

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze how tool results stream into the current chat UI. Identify where tool calls and tool results can be displayed without rewriting the whole chat system.

R: Hermes needs visible activity telemetry so users trust what it is doing.

P: Implement Phase 7 only.

Task:
Add tool activity UI.

Requirements:
- Display a compact activity card when Hermes uses a tool.
- Show:
  - tool name
  - status: pending, completed, failed, confirmation required
  - short summary
  - safety notice for write/dev-command tools
- For propose_file_edit:
  - show diff preview
  - show approve/reject actions
- For run_dev_command:
  - show commandId, not raw shell
  - show output summary with expand option
- For read tools:
  - show file path read/listed
- Do not expose hidden stack traces.
- Do not clutter normal chat when no tools are used.

Tests:
- Tool call renders
- Failed tool renders safe error
- Confirmation-required state renders
- Existing normal chat still renders

A: Stop after implementation and report:
1. Files changed
2. UI behavior
3. Tests run
4. Screenshots or description of expected UI states

Do not continue to Phase 8.”

Behavior preserved + tests to run:
- Normal chat still looks normal.
- Tool activity is visible but not noisy.
- Run:
  - npm run typecheck
  - component tests, if present
  - chat transport tests

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add SpiritOS tool activity UI”

Success criteria:
- User can see what Hermes is doing.
- Edits require visible approval.
- Tool failures are understandable.
- No secret data is shown.

==================================================
PHASE 8: EVALUATION HARNESS AND ANTI-HALLUCINATION TESTS
==================================================

Goal:
Make sure Hermes does not lie about capabilities, fake tool results, or claim actions it did not perform.

Exact files to touch:
- tests/evals/spirit-capabilities.test.ts, new
- tests/evals/tool-hallucination.test.ts, new
- src/lib/spirit/system-state.ts
- src/lib/spirit/model-runtime.ts
- Possibly test fixtures

Files not to touch:
- Do not add new runtime features
- Do not change UI
- Do not change tools unless a bug is found

Precise Cursor prompt:

“Work in ARPA mode.

A: Analyze current test setup and determine where evaluation-style tests should live.

R: The intelligence overhaul needs anti-hallucination checks. Hermes must know what tools are available, unavailable, enabled, disabled, and actually executed.

P: Implement Phase 8 only.

Task:
Add evaluation tests for capability honesty.

Tests should verify:
1. When tools are disabled, system prompt lists terminal_execution and file_editing as unavailable.
2. When read-only tools are enabled, system prompt lists only read-only tools as available.
3. When write tools are disabled, Hermes should not be instructed that it can edit files.
4. When dev-command tools are disabled, Hermes should not be instructed that it can run commands.
5. Tool result messages are distinguishable from model-generated claims.
6. The prompt includes “do not claim tool use unless a tool actually returned a result.”
7. The route does not expose tools when env flags are false.
8. Blocked paths remain blocked.

Optional eval fixtures:
- User asks “edit this file” when editing disabled.
- Expected behavior: Hermes says editing is unavailable or offers a manual patch.
- User asks “run npm test” when dev commands disabled.
- Expected behavior: Hermes says command execution is unavailable.

A: Stop after implementation and report:
1. Files changed
2. Eval coverage
3. Tests run
4. Any weak areas still needing manual testing”

Behavior preserved + tests to run:
- No new behavior except tests.
- Run:
  - npm run typecheck
  - eval tests
  - full test suite if feasible

Rollback point:
- Commit after success:
  - git add .
  - git commit -m “add SpiritOS capability honesty evals”

Success criteria:
- Hermes has tests against tool hallucination.
- Disabled tools stay disabled.
- System prompt accurately reflects capabilities.
- Future phases are safer to build on.

==================================================
PHASE 9: LONG-TERM SOVEREIGN OS POLISH
==================================================

Goal:
Only after the foundation is stable, begin making Hermes feel like a real operating intelligence instead of a chatbot.

Exact files to touch:
- Depends on prior phases
- model-runtime
- system-state
- memory bridge
- UI activity components
- diagnostics panel
- Oracle UI

Files not to touch:
- Do not rewrite everything at once
- Do not remove stable features without replacement
- Do not collapse all prompts into one mega-prompt

Precise Cursor prompt:

“Work in ARPA mode.

A: Review Phases 1 through 8 and confirm all tests pass.

R: Now that dynamic context, soft routing, optional memory, safe tools, guarded edits, dev commands, telemetry, and evals exist, plan the next intelligence polish layer.

P: Propose improvements only. Do not code yet.

Areas to evaluate:
1. Should model profiles become hidden presets instead of user-facing modes?
2. Should Oracle memory become user-toggleable in settings?
3. Should Hermes have project-specific memory?
4. Should there be a live system dashboard showing model, tools, memory, and active capabilities?
5. Should there be a “task mode” where Hermes plans, acts, verifies, and summarizes?
6. Should dev commands support more allowlisted commands?
7. Should file edits support patch-based edits instead of full-file writes?

A: Ask permission before implementing any polish phase.”

Behavior preserved + tests to run:
- All previous tests.
- No implementation yet.

Rollback point:
- No code changes.

Success criteria:
- You have a stable next roadmap.
- No fragile big-bang refactor.
- Hermes evolves from chatbot into SpiritOS brain safely.

==================================================
MASTER IMPLEMENTATION ORDER
==================================================

Recommended commit sequence:

1. repo contract audit
2. add dynamic SpiritOS system state
3. add soft semantic persona routing
4. add optional Oracle memory bridge
5. add safe read-only SpiritOS tools
6. add guarded SpiritOS file edit tools
7. add allowlisted SpiritOS dev command tools
8. add SpiritOS tool activity UI
9. add SpiritOS capability honesty evals
10. polish sovereign OS behavior

==================================================
FINAL RULE FOR EVERY CURSOR SESSION
==================================================

Every Cursor session must end with:

1. What changed
2. What files changed
3. What behavior was preserved
4. What tests were run
5. What failed, if anything
6. What rollback commit exists
7. What the next phase is
8. Ask permission before moving on