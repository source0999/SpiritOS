# Gate 2-J.9 Sealed Inference Bridge Specification

status: `ATTESTING_LOOPBACK_BRIDGE_SPECIFIED_PENDING_IMPLEMENTATION`

schema: `source-proxy.gate-2j-9-inference-bridge-specification/v1`

The current `network_bridge.py` + `loopback_bridge_runner.py` is a byte-forwarding relay:
it connects the sandbox loopback listener to one host loopback endpoint and copies bytes
both ways. It deliberately does not inspect, attest, or enforce. The sealed dispatcher
requires an **attesting** bridge layered on this transport.

## 1. Permitted flow

```text
JCode (sandbox, no net namespace, loopback only)
  -> local sealed inference bridge (attesting proxy-controlled)
     -> authorized inference-only proxy endpoint (http://127.0.0.1:4000/v1)
        -> exact selected local model (qwen2.5-coder:7b | :14b)
```

## 2. Forbidden flows (bridge MUST reject)

- JCode -> `/coding` (the production orchestration route). The bridge must never forward to
  the Source Proxy coding route.
- JCode -> an arbitrary external provider (any host other than the permitted loopback endpoint).
- JCode -> an unregistered model fallback (any model id other than the lane's expected id).
- Recursion: a bridge request whose target resolves back to the bridge itself.

## 3. Bridge duties (enforced per request)

For every HTTP request transiting the bridge:

- accept requests only from the active contained task (bind by the run's cgroup/socket identity);
- bind the request to task ID and correlation ID (injected/verified header);
- verify the authorized provider profile `spiritos-qualification` and the permitted endpoint;
- verify the authorized model equals the lane's expected model id (primary `qwen2.5-coder:7b`
  or challenger `qwen2.5-coder:14b`); reject unknown models; reject direct fallback;
- enforce generation parameters (max_tokens <= 4096, seed == 7, temperature == 0, top_p/top_k
  within envelope; reject out-of-range);
- enforce request budget (increment a per-run counter; reject when request-count max reached);
  and token budget (sum usage across responses; reject/fail when token max reached);
- capture complete request metadata (method, path, headers minus secrets, body hash, timestamp);
- capture complete response metadata (status, provider-reported model id, usage, streaming
  termination reason, response body hash);
- capture provider-reported model identity and reconcile via `identity.reconcile_jcode_model_identity`;
- reject malformed or incomplete tool-call streams (truncate/fail closed);
- fail closed when identity cannot be proven (no response forwarded to JCode, no success emitted).

## 4. Evidence output

The bridge writes, per run, into the evidence directory:

- `model-request-ledger.ndjson`: one record per request with task/correlation id, model,
  generation params, request body hash, response status, provider-reported model, usage,
  termination reason, timestamp.
- `model-response-metadata.json`: aggregate provider-reported identity + usage totals.
- These feed `evidence_hashes` in the sealed envelope.

## 5. Implementation boundary

- Transport reuse: the existing `FixedLoopbackUnixBridge` / `loopback_bridge_runner.py`
  remains the byte path *inside* the sandbox. The attestation layer is a Proxy-side HTTP
  interceptor on the host loopback endpoint (not inside the sandbox).
- The attesting bridge is a new module `source_proxy/jcode/sealed_inference_bridge.py`.
- It does not call the production `/coding` route. It dials only `http://127.0.0.1:4000/v1`.
- No production credentials are stored or forwarded (no-auth policy).

## 6. Gate sequencing

- Gate 2-J.9F: implement against a **fake model endpoint** (fixture) proving attestation,
  enforcement, and rejection of all forbidden flows. No real model.
- A single no-op **real** local-model identity probe is permitted at Gate 2-J.9F ONLY if the
  operator seals decision #5 in the architecture spec. Default: real probe deferred to 2-J.9H.
- Gate 2-J.9H: one real contained model smoke test under separate operator authorization.
