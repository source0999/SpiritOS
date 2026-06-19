# Operator Summary

What Britton should see now in Batch smart:

- Count-card explainer saying rename previews appear after tags/metadata are reviewed or approved.
- Each item row shows analysis status, review status, tag count, approved/rejected/pending counts, and a safe analysis sidecar reference.
- Tags are visible as chips with label, confidence, group styling, review-required marker, and review state.
- Rows show proposed filename when available.
- Rows explain whether the rename preview is ready, provisional, blocked, missing a suggestion, or unavailable.
- Rows show why rename preview is blocked, including unreviewed metadata, unsafe names, duplicate target paths, or existing target conflicts.
- Item actions are visible: approve this item, reject this item, mark this reviewed, refresh this item.
- Real rename/move apply remains disabled and explicitly says future Britton approval is required.

What to test next:

- Open `/spiritflix/admin`.
- Open a folder with current smart analysis sidecars.
- Click Batch smart, then Preview folder or Analyze folder.
- Confirm unreviewed videos show tags and provisional names.
- Click Approve this item or Approve tags, then inspect that rename previews become available where names are safe.
- Click Rename plan and verify ready/blocker counts match the row details.

No media rename, media move, Jellyfin mutation, Source Proxy work, model call, OCR, or VLM lane was performed.
