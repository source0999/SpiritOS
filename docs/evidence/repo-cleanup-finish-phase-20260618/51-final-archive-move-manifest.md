# Final Archive/Move Manifest

Result: NEEDS_APPROVAL. Nothing was moved or archived.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/

- Category: closed evidence packet
- Size estimate: 3.5M
- Reason: Prior cleanup audit packet reviewed and superseded by finish-phase summary for active context purposes.
- Risk: medium
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-host-cleanup-stability-audit-20260617/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-host-cleanup-stability-audit-20260617/ && mv -- docs/evidence/repo-host-cleanup-stability-audit-20260617/ /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-host-cleanup-stability-audit-20260617/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-host-cleanup-stability-audit-20260617/* docs/evidence/repo-host-cleanup-stability-audit-20260617/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## docs/evidence/repo-cleanup-manifest-watchers-20260617/

- Category: closed evidence packet
- Size estimate: 760K
- Reason: Prior watcher/cleanup manifest packet reviewed; useful for archive but noisy for active context.
- Risk: medium
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-cleanup-manifest-watchers-20260617/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-cleanup-manifest-watchers-20260617/ && mv -- docs/evidence/repo-cleanup-manifest-watchers-20260617/ /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-cleanup-manifest-watchers-20260617/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/repo-cleanup-manifest-watchers-20260617/* docs/evidence/repo-cleanup-manifest-watchers-20260617/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## docs/evidence/live-hiccup-triage-20260617/

- Category: closed evidence packet
- Size estimate: 412K
- Reason: Old live hiccup triage evidence; not part of current Source Proxy return surface.
- Risk: medium
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/live-hiccup-triage-20260617/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/live-hiccup-triage-20260617/ && mv -- docs/evidence/live-hiccup-triage-20260617/ /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/live-hiccup-triage-20260617/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/live-hiccup-triage-20260617/* docs/evidence/live-hiccup-triage-20260617/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## docs/evidence/source-proxy-glm-3x10-audit-20260617/

- Category: Source Proxy evidence packet
- Size estimate: 544K
- Reason: Source Proxy audit evidence should be preserved; archive only if Britton wants active context reduced and provenance retained.
- Risk: high
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-glm-3x10-audit-20260617/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-glm-3x10-audit-20260617/ && mv -- docs/evidence/source-proxy-glm-3x10-audit-20260617/ /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-glm-3x10-audit-20260617/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-glm-3x10-audit-20260617/* docs/evidence/source-proxy-glm-3x10-audit-20260617/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-*.json

- Category: old repeated receipts/traces
- Size estimate: 164M
- Reason: Untracked FIP receipt JSON files; preserve if archived, do not delete during cleanup.
- Risk: high
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/ && mv -- docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-*.json /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/* docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## scripts/media/face_*.html scripts/media/*audit.html scripts/media/manual_crop.html

- Category: generated report HTML
- Size estimate: 13G
- Reason: Generated face-organizer report HTML is large/noisy and already causes diff-check whitespace noise.
- Risk: high
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/ && mv -- scripts/media/face_*.html scripts/media/*audit.html scripts/media/manual_crop.html /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/* scripts/media/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context

## scripts/media/face_*.json scripts/media/*audit.json scripts/media/performer_verification.json

- Category: generated report JSON
- Size estimate: 13G
- Reason: Generated report/model evidence should be preserved but kept out of active source context if approved.
- Risk: high
- Proposed destination: `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/`
- Exact command later if approved: `mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/ && mv -- scripts/media/face_*.json scripts/media/*audit.json scripts/media/performer_verification.json /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/`
- Rollback command: `mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260618/scripts/media/reports/* scripts/media/`
- Affects git: yes, if tracked/dirty paths are moved; requires review before execution
- Scope effect: actual repo tree and repomix context
