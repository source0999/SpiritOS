# Operator Summary

Batch Smart now samples frames and asks the local visual model for review-required content tags. The operator can review/edit tags and display name suggestions, then use `Confirm approved tags and name` to write SpiritFlix metadata sidecars.

Confirm writes approved tags, `displayTitle`, `displayNameOverride`, `smartDisplayName`, `smartTagIds`, and the full `smartApproved` projection. It does not rename, move, delete, restart services, or mutate Jellyfin config/database.
