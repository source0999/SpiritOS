# Global Correction Confirmation

## Authorization

Receipt type: `AUDIT_REMEDIATION_RECEIPT`

Remediation ID: `C2J-GLOBAL-CORRECTION-01`

The correction is bound to operator authorization
`OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1` and prompt SHA-256
`f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`.

## One Correction

The isolated diagnostic bridge was switched from lossy prompt-only
OpenAI-chat-to-Ollama-generate translation to a role/tool-preserving
OpenAI-chat-to-Ollama-chat profile. It preserves ordered messages and native
schemas, maps tool-result names, and reconstructs assistant content or native
tool calls as OpenAI-compatible SSE.

No task, source, test, acceptance criterion, model, digest, JCode binary,
prompt, workspace policy, network policy, turn cap, or production default was
changed. Legacy mode remains the default. No production or daily-runtime file
was mutated.

## Confirmation Cells

| Run | Model/task | Roles/tools preserved | Model behavior | JCode tool events | Pass |
| --- | --- | --- | --- | ---: | --- |
| `s3-r-dtp-7b` | 7B / R | Yes | Promises to read; asks for further instruction | 0 | No |
| `s3-r-dtp-14b` | 14B / R | Yes | Fenced JSON `read` of task packet | 0 | No |
| `s3-w-dtp-7b` | 7B / W | Yes | Fenced JSON `read` of task packet | 0 | No |
| `s3-w-dtp-14b` | 14B / W | Yes | Fenced JSON `read` of task packet | 0 | No |

Each run used one request, so confirmation consumed four requests and no retry.
All exact requests and responses are complete and hash-sealed.

## Decision

The bridge correction improves behavior consistently at its target boundary:
all four cells change from flattened prompt/no tools to preserved
`system,user,user` messages and unchanged tools. It does not produce an
end-to-end pass. The new first failure is the Qwen text-tool dialect plus
JCode's native-only parsing; Task W would also remain blocked by the absent
focused-test tool.

Therefore:

- bridge counterfactual: PASS;
- full confirmation task result: FAIL in 4 of 4;
- production promotion: NOT AUTHORIZED;
- campaign outcome: `PIPELINE_NOT_READY_FOR_COMPARISON`;
- next required work: implement and qualify the complete Gate 2-J.9T packet,
  parser/recovery, and tool profile under new execution authorization.
