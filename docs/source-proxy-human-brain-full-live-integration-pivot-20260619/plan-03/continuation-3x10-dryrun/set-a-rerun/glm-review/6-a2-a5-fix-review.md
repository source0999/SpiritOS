# Stage 6 — A2 / A5 Fix Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

Context: the prior review failed A2 and A5 on `research_materially_changed_output`. The 4R fix (`4r-fix-runner-change.md`, `4r-fix-validation.md`) claims to have rerun only A2 and A5 via `PLAN3_STAGE4R_ONLY`, strengthened the model prompt to require a `Research findings that changed the plan` section, and tightened materiality grading. Both now report PASS. `auto_fix_attempts`: A2=0, A5=0 (i.e., passed on the first attempt after the fix), A6=2, A9=1.

## A2 — browser extension

- **Did A2 actually rerun?** Yes, as far as in-repo artifacts show. New `task_id=task_67febc3fbc6e`, `trace_id=trace_25974aed640f474e`, `latest_consumer_event_id=consumer_49e7c01400c04257`. These are not old-set IDs.
- **task_id / consumer_event_id new?** Yes — distinct from old `set-a/A2` and distinct from every other rerun record.
- **Did the final work product materially use in-run extension research?** **Partially.** The recommendation (Native Messaging API + a native host process) is correct and is consistent with current MV3 reality (MV3 service workers can still use `chrome.runtime.connectNative`; the sources confirm this). The three `Finding:` bullets are real findings (native messaging permission, host executable concept, message-passing parity). So the direction is research-shaped.
  - However, the materiality section is **degraded by hallucinated/corrupted domains**: `dexevelopeer.chrome.com` and `dexevelopeer.mozilla.org` (the model corrupted `developer`→`dexevelopeer`). The correct domains survive only in the separate "Actual Research/Search Evidence" list. The grader passed on the *surviving* host fragments (`stackoverflow.com`, `learn.microsoft.com`, `textslashplain.com`).
- **Did it reference repo task endpoints/context?** Yes — Evidence Used lists `source_proxy/api/long_running_tasks.py`, `task_spec_intake.py`, `src/app/v1/tasks/long-running/route.ts` (twice), `durable_execution.py`. These are real files and `repo_files_read` matches `REPO_SURFACES["A2"]`.
- **Is it useful for an agent to implement next?** Yes, moderately: it identifies the Native Messaging host pattern and names the receiver endpoint. But it gives no manifest sketch, no native-host registration specifics, no MV3 service-worker lifecycle caveat, and no message-format/length-limit detail that the research would have supplied. A stronger, genuinely-research-shaped answer would include the 1 MB message cap and the `nativeMessaging` manifest permission explicitly in the plan (the sources mention these).
- **Fix-real assessment:** The fix made A2 emit the structured materiality template, which is an improvement over the old canned draft, but the gate passed corrupted-domain echo. The recommendation is sound; the *evidence of materiality* is weak.

**A2_FIX: NEEDS_FIX** — the recommendation is acceptable, but materiality evidence is corrupted-domain echo and the plan omits the specific MV3 constraints the research actually contained. Borderline; would be acceptable if the grader were honest.

## A5 — local AI workstation (Dell/Mac/Windows)

- **Did A5 actually rerun?** Yes. New `task_id=task_9894ad793a6e`, `trace_id=trace_0f3e35a36e92496d`, `latest_consumer_event_id=consumer_01c500efc5af495e`. Fresh IDs.
- **task_id / consumer_event_id new?** Yes.
- **Was Mac evidence non-system_status and consumed?** **NO — this is the core unresolved failure.**
  - Runner L462: `run_mac_worker_for_task(task_id, mode="mac_safe_check", input_data={"check_command": "python3 --version", "purpose": "Stage 4R A5 workstation capability readback"})`.
  - `mac_integration.py` maps `mac_safe_check` → job_type `run_safe_check`. The grader gate (L236) is `mac_status == "INTEGRATED_LIVE" and mac_job_type != "system_status"`. Because job_type is `run_safe_check` (not `system_status`), the gate passes.
  - But `python3 --version` is a **capability readback** that proves the Mac can run a Python interpreter. It says nothing about Mac fitness for the local-AI workload (GPU, unified memory, model sizes), nothing about Dell's role, nothing about Windows/WSL. This is the identical proof class the prior review rejected under cheat #14 ("A5 passes from Mac system_status alone") and #15 ("A5 claims Mac validation but only performed a generic ping"). Renaming `system_status`→`run_safe_check` and swapping the SSH status command for `python3 --version` does not change what was proven.
  - Consequently `mac_system_status_alone_used_as_pass=false` is **misreported**: the pass does rest on a trivial capability ping.
- **Did the final plan use Mac evidence honestly?** **No.** The "Evidence Used" section lists `mac_integration.py`, `mac_intregation.py` (typo), `mac-worker/route.ts`, and "Mac worker evidence: … confirms the successful execution of a `run_safe_check` job." That is a description of plumbing, not workstation evidence. It then asserts "the `spirit-mac-mini` node is the worker" and routes Ollama to it — a claim the `python3 --version` ping cannot support.
- **Did in-run research materially shape Dell/Mac/Windows role choices?** **No.** The user explicitly asked for a plan across **Dell, Mac, and Windows** "without wasting money." The plan collapses "Dell Mac" into a single machine, assigns Ollama to `spirit-mac-mini`, never gives Dell or Windows distinct roles, gives no cost guidance, and ignores the homelab-GPU / Docker+AMD findings that were in the source list and that *should* have driven a cost-aware three-machine split. The three `How it changed the plan` bullets are decorative restatements ("Prioritizes LM Studio…", "Incorporates Ollama…", "Confirms viability…"), not decisions changed by findings.
- **Did it avoid claiming proof it does not have?** **No.** It claims the Mac integration "is functioning" and routes production LLM traffic to `spirit-mac-mini` on the basis of a `python3 --version` readback. That is an overclaim.

**A5_FIX: NEEDS_FIX.** The rerun produced fresh IDs and a live model answer, but:
1. Mac "validation" is still a trivial capability ping (cheat #14/#15 carried forward under a new job_type).
2. The recommendation does not address the actual three-machine, cost-aware user goal.
3. Materiality is decorative echo, not research-shaped decisions.
4. It overclaims Mac integration fitness.

This is the same A5 failure as before, with a renamed job_type. The fix did not resolve the substance.

## Verdict

```
A2_FIX_ACCEPTED | A2_FIX_NEEDS_FIX   →  A2_FIX_NEEDS_FIX
A5_FIX_ACCEPTED | A5_FIX_NEEDS_FIX   →  A5_FIX_NEEDS_FIX
```

A2 is close (recommendation is right) but its materiality evidence is corrupted and under-specified. A5 is not fixed in substance: the Mac proof is a renamed ping and the plan dodges the actual Dell/Mac/Windows cost question. Neither previously-failing prompt was honestly resolved.
