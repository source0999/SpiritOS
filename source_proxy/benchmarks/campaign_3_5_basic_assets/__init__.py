"""Private assets for the Source Proxy Basic Backend 10 gate.

This package may be imported by the benchmark harness and focused tests only.
Production planner, coder, reviewer, verifier, and target-plugin modules must
not import it.  In particular, oracle and reference details never cross the
production dispatch boundary.
"""

ASSET_VERSION = "source_proxy_basic_backend_10_assets_v1.0.0"
