# Gate 2-J.9G-B Sealed-Bridge Retry V2 Receipt

## Verdict

BLOCKED_BEFORE_COMPLIANT_FAKE_BRIDGE_REQUEST

## Preconditions

Gate 2-J.9G-S passed at b02301cc3. The root now provides a fresh writable
tmpfs JCODE_HOME, and an absent-listener launch reaches the configured
OpenAI-compatible endpoint with ECONNREFUSED. This excludes the original
read-only-home startup failure.

## Retry Result

A static loopback-only shim bound 127.0.0.1:43123 inside the unshared network
namespace and was connected to a Proxy-owned host bridge through an inherited
socketpair. The exact binary was launched with the sealed base URL, expected
model, and task-scoped capability. The wrapper did not terminate or produce a
provider request within the 45-second supervisor timeout.

This retry produced no fake request, no real model request, no direct Ollama
request, no repository mutation, and no network-policy relaxation. The
prototype shim and host adapter were removed rather than being accepted on the
strength of an unproven path.

## Stop Condition

The integration stage requires complete JCode-to-fake-backend evidence. That
evidence is absent, so 2-J.9G and 2-J.9H are not started. A future
authorization must instrument the shim's accept/read/channel states and the
exact JCode HTTP framing without adding a broader host network path.
