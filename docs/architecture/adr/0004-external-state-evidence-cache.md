# ADR 0004: External state, evidence, and cache roots

Decision: generated evidence and cache output use configured external roots; mutable service state is not migrated in Campaign 1.
Reason: tracked evidence dominates repository context while runtime state needs preservation-first handling.
Consequences: byte manifests, sensitive-data scans, archive readability, and rollback are required.
Campaign 2 dependency: mutable runtime-state migration.
Revision condition: external storage cannot provide byte-for-byte recoverability.