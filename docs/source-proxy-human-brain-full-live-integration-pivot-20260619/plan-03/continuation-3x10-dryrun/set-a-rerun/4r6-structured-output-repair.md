# Stage 4R6 Structured Output Repair

- Ollama JSON/format mode is attempted by the packet call. If it returns an empty response or unusable JSON, the runner falls back to prompt-only JSON and then repair prompts.
- Invalid JSON is not edited by the script. The raw invalid output, parse error, and validation errors are passed back to the live model for a corrected JSON object.
- Every packet attempt is written to raw evidence as `<prompt>.decision_packet.attempt<N>.raw.json`; repair attempts are also written as `<prompt>.decision_packet.repair<N>.raw.json`.
- The script may strip fences or prose around an intact JSON object, parse it, and validate it. It does not fill in missing decisions, sources, Mac conclusions, recommendations, or limits.
- The deterministic renderer runs only after packet validation succeeds; the hardened grader still decides final status.
