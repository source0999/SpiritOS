# Boundary enforcement

Campaign 1 uses **ESLint import restrictions** as its one minimum dependency-boundary enforcement tool. It is already part of the Next toolchain, so it introduces no second graph tool or workspace orchestrator.

- Contract sources may not import product runtime code.
- Production TypeScript may not import `labs/` or test/fixture roots.
- Coding and SpiritFlix product roots may not import one another's product-specific roots.

Python contract validation reads JSON Schema from this package and has no product-runtime imports. Python remains the lifecycle authority; the Next consumer only maps transport casing and validates schemas before rendering.
