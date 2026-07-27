# Gate 2-J.3 Network and Credential Containment

status: `GREEN_OS_ENFORCED_SINGLE_ENDPOINT`

## Boundary

The JCode command remains in Bubblewrap's `--unshare-net` namespace. It cannot
directly reach the host network, including the host's loopback inference port.
The only network capability exposed to that namespace is a local TCP listener
on `127.0.0.1`. The listener is a trusted relay that can connect only to one
read-only Unix-domain socket. The host-side bridge for that socket accepts one
configured `127.0.0.1` or `::1` endpoint and port; it rejects non-loopback
endpoints before listening.

The bridge does not inherit or forward credentials, does not expose a host
network namespace, and does not permit a configurable destination from the
sandbox. Its socket directory must contain exactly `inference.sock` and is
read-only inside Bubblewrap. This is a qualification primitive, not a JCode
dispatcher or a production integration.

## Executed evidence

| Check | Result |
|---|---|
| Focused command | `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_jcode_network_bridge.py source_proxy/tests/test_jcode_containment.py source_proxy/tests/test_jcode_qualification_adapter.py source_proxy/tests/test_bubblewrap_sandbox.py` |
| Result | `53 passed in 1.42s` |
| Positive OS proof | A Bubblewrap process fetched a response from a test loopback inference server through `sandbox TCP -> Unix socket -> fixed host loopback` only. |
| Negative OS proof | The same process attempted the host server's actual loopback port directly and received a nonzero `connect_ex` result before using the relay. |
| Configuration proof | Non-loopback endpoint and non-dedicated socket-directory inputs fail closed. |

## Disposition

Gate 2-J.3 is complete. Earlier investigation established that direct firewall
management is not available to this worker; the Unix-socket bridge avoids that
privilege requirement without weakening the no-network namespace. No real
model, provider, credential, task, or daily runtime endpoint was invoked.

Gate 2-J.4 process supervision may begin. `JCODE_EXECUTOR_ENABLED` remains
disabled and the default executor remains unchanged.
