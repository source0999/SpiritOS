# Stage 4R3 Runner Change

- Added a per-prompt evidence digest step for selected A2/A5/A9 reruns.
- The digest is built from raw in-run research sources, repo context, and Mac capability evidence where applicable.
- The digest is also read by the live model as an intermediate evidence-to-decision pass and written to raw evidence as `<prompt>.evidence_digest.raw.json`.
- Final generation now receives canonical source citations and exact source hosts to prevent model-spelled fake domains.
- Final generation is instructed to synthesize from the digest, not copy it, and to produce non-JSON/non-table research-to-decision bullets.
- This improves generation quality by giving the live model a clean evidence map before the final packet.
- This does not weaken the hardened Stage 4R2 grader; grader gates, adversarial selftest, `final_status`, and `fake_go_detected` computation remain in force.
- This is not canned output: sources, repo snippets, Mac facts, and digest content are created from the live rerun evidence for each prompt.
