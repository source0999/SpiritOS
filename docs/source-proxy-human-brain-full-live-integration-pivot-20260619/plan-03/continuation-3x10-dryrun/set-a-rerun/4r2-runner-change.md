# Stage 4R2 Runner Change

- Hardened research materiality so source-name/domain echo is not enough.
- Added research-to-decision block parsing with concrete Finding, Source, Decision changed, and Why fields.
- Rejected generic materiality phrases and garbled/fabricated tokens such as `dexevelopeer`, `local_l`, non-English corrupted fragments, and `vlvm`.
- Added A2-specific gates for MV3, nativeMessaging permission, native-host registration, service-worker lifecycle, payload/local API boundaries, Source Proxy endpoint/repo context, safe MVP, and coding-agent handoff.
- Added A5-specific gates for Dell/Mac/Windows role split, cost/no-new-hardware reasoning, privacy/local/cloud tradeoff, role-tied tooling, and two-signal non-trivial Mac evidence.
- Added A9-specific gates for clean comparison of real current local LLM tools, recency limitations, proxy-specific recommendation, and no fabricated names.
- Kept `PLAN3_STAGE4R_ONLY=A2,A5,A9` selective rerun support; unselected A1/A3/A4/A6/A7/A8/A10 records are preserved and only summary aggregation is refreshed.
- Kept `final_status` grader-derived and `fake_go_detected` computed.
