# Visual Proof

Date: 2026-05-30
Branch: lane/coding-human-trial-runner-polish-20260530-112512

Rendered UI evidence from focused React tests:

- `/coding` route renders `CodingCockpitShell`.
- New chat is visible.
- Task Composer is visible with one prompt textarea.
- Trial runner is visible.
- Trial category dropdown is visible with `Coder`, `Designer`, and `Combined`.
- Trial count dropdown is visible with exactly `10`, `25`, `50`, and `100`.
- Copy prompts is visible.
- Copy trial diagnostics is visible.
- Right panel shows current task, model, state, changed files, checks, copy current task diagnostics, and copy trial diagnostics.
- Advanced details is not visible in the normal tested shell.

Local app server note:

- `npm run dev` reported an existing Next dev server for this repo on port 3000 and refused to start a second server.
- Fetching `http://localhost:3000/coding` from Node failed because the existing server closed the socket.
- I did not kill the existing dev PID because cleanup/server interruption was not part of the approved action.

Result: UI structure is covered by focused tests, but live browser visual proof is NO-GO until the existing dev server is restarted or made reachable.
