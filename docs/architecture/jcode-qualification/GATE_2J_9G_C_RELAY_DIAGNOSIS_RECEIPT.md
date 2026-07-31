# Gate 2-J.9G-C Relay Diagnosis

Verdict: BLOCKED.

The in-root listener successfully bound 127.0.0.1:43123 before the exact
contained JCode child was launched. Its accept loop received no connection in
the 40-second bounded diagnostic window, and the inherited event channel
received no accept event. No fake backend or real provider was invoked.

This identifies the first missing transition as JCode connect while launched
as a child of the relay parent. The prior direct contained launch with the same
fresh home, provider environment, and endpoint reached connect and returned
ECONNREFUSED. Therefore HTTP framing, Content-Length, Expect handling, and
the relay channel are not reached; a standards-compliant protocol correction
would be speculative.

Classification: CONNECT_NOT_ATTEMPTED / CONTAINMENT_INTERACTION. The relay
prototype is removed. Gates 2-J.9G-B, 2-J.9G, and 2-J.9H are not started.
