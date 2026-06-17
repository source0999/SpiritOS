# SpiritFlix Admin Explorer Plan - Level 1 + Level 2

## Status

Planning document only.

This document is not implementation approval. It records the approved direction for a future SpiritFlix admin media explorer.

Implementation must happen in later Pivot Workflow phases after Britton explicitly approves the next implementation prompt.

## Goal

Build a private SpiritFlix admin page that replaces the weak CasaOS media-management experience for SpiritFlix videos.

The admin page should let Britton browse, search, sort, inspect, organize, reorder, and eventually safely modify SpiritFlix media without leaving SpiritOS.

This is not a CasaOS clone. This is a SpiritFlix-native media explorer/admin lane designed around Jellyfin libraries plus the real `/mnt/spirit-8tb/media` filesystem layout.

## Core problem

The current CasaOS page is too basic for managing SpiritFlix media:

* hard to sort videos by date added
* hard to inspect folders
* hard to add folders
* hard to find media quickly
* no real SpiritFlix-aware explorer
* no clean CRUD workflow for media organization
* no custom ordering/reordering lane for shelves/playlists
* no good receipt trail for actions

SpiritFlix already has a viewer/player experience. What is missing is the admin/explorer side.

## Product shape

Add a private admin route in a later implementation phase:

```text
/spiritflix/admin
```

Keep it separate from the normal viewer route:

```text
/spiritflix
```

The viewer stays focused on watching. The admin route focuses on managing.

## Scope boundaries

Stay inside the SpiritFlix/Jellyfin lane.

Likely future implementation areas:

```text
src/app/spiritflix/admin/page.tsx
src/components/spiritflix/admin/
src/app/api/spiritflix/admin/
src/lib/spiritflix/admin/
docs/media/spiritflix-admin-explorer-plan.md
```

Do not infer or rewrite unrelated SpiritOS modules unless a later implementation phase proves they are imported and necessary.

Do not expose Jellyfin or the admin lane publicly.

Jellyfin remains private Tailscale/LAN access only.

Do not mutate Jellyfin SQLite directly.

Do not hard delete media in Level 2.

Do not bypass DRM or add unauthorized download behavior.

## Level 1 - Read-only Admin Explorer

Level 1 must be read-only. No moving, deleting, renaming, creating folders, or rewriting metadata yet.

### Level 1 goals

Build a usable admin explorer that can show all SpiritFlix media in a table/grid with powerful search and sorting.

### Level 1 features

#### 1. Admin route

Future implementation should create:

```text
src/app/spiritflix/admin/page.tsx
```

Future admin components should live under:

```text
src/components/spiritflix/admin/
```

Suggested components:

```text
SpiritFlixAdminApp.tsx
SpiritFlixAdminExplorer.tsx
SpiritFlixAdminTable.tsx
SpiritFlixAdminToolbar.tsx
SpiritFlixAdminDetailsPanel.tsx
SpiritFlixAdminBreadcrumbs.tsx
SpiritFlixAdminFilters.tsx
```

#### 2. Read-only admin API

Future implementation should create a read-only API namespace:

```text
src/app/api/spiritflix/admin/library/route.ts
src/app/api/spiritflix/admin/fs/route.ts
```

The API should return normalized admin records, not raw messy Jellyfin-only objects.

Suggested item shape:

```ts
interface SpiritFlixAdminItem {
  id: string;
  name: string;
  type: "file" | "folder" | "jellyfin-item";
  libraryName?: string;
  jellyfinId?: string;
  path?: string;
  parentPath?: string;
  jellyfinPath?: string;
  mediaType?: string;
  itemType?: string;
  extension?: string;
  sizeBytes?: number;
  dateCreated?: string;
  dateModified?: string;
  dateAdded?: string;
  runtimeTicks?: number;
  watched?: boolean;
  favorite?: boolean;
  hasImage?: boolean;
  playable?: boolean;
}
```

#### 3. Jellyfin-backed item listing

Use existing Jellyfin session/client patterns where possible.

Support:

```text
searchTerm
libraryId
parentId
recursive
sortBy
sortOrder
limit
startIndex
includeItemTypes
```

Important Level 1 sorts:

```text
Date Added newest first
Date Added oldest first
File Modified newest first
File Modified oldest first
Title A-Z
Title Z-A
Runtime long-short
Runtime short-long
Size large-small
Size small-large
Folder/path
Library
Watched/unwatched
Favorite
```

#### 4. Filesystem folder explorer

Add read-only folder browsing for allowlisted roots.

Initial allowed roots:

```text
/mnt/spirit-8tb/media
/mnt/spirit-8tb/media/anime
/mnt/spirit-8tb/media/movies
/mnt/spirit-8tb/media/tv
/mnt/spirit-8tb/media/music
/mnt/spirit-8tb/media/other
/mnt/spirit-8tb/media/yes
/mnt/spirit-8tb/media-inbox
```

Do not expose arbitrary filesystem access.

The API must reject:

```text
..
absolute paths outside allowed roots
symlink escape
hidden/system paths unless explicitly allowlisted
Jellyfin config paths
.env files
repo secrets
```

#### 5. Search all

The admin page should have one search box that can search:

```text
Jellyfin item title
folder name
file name
path segment
library name
extension
model/person metadata if available
```

#### 6. Detail panel

Clicking an item opens a right-side details panel.

Show:

```text
title/name
library
path
parent folder
Jellyfin item ID
media type
item type
duration
file size
date added
date created
date modified
watched/favorite
resume position if available
image/poster if available
known face/model metadata if available
```

Read-only buttons:

```text
Copy path
Copy filename
Copy Jellyfin ID
Open in SpiritFlix viewer
Open folder in admin explorer
Refresh listing
```

#### 7. UI expectations

The admin page should feel like a lightweight media operating system:

```text
left sidebar: roots/libraries
top toolbar: search, sort, filters, view toggle
main panel: table/grid
right panel: details
bottom/status area: count, selected count, current root, last refresh
```

Mobile should still work on Fold-style devices:

```text
table turns into cards
details panel becomes bottom sheet
toolbar wraps cleanly
large tap targets
```

#### 8. Level 1 non-goals

Do not implement write actions in Level 1.

No rename.
No move.
No folder creation.
No delete.
No metadata writes.
No reorder persistence.
No library rescan mutation unless exposed as disabled/preview only.
No public network exposure.
No changing Jellyfin config.
No hard delete.

#### 9. Level 1 verification

Required checks for the future implementation phase:

```bash
npm run typecheck
vitest run src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
```

Add focused tests for:

```text
admin route renders
admin toolbar search updates query
sort controls change sort mode
details panel opens on item click
filesystem API rejects path traversal
filesystem API rejects outside allowed root
admin API returns stable normalized item shape
```

Level 1 pass condition:

```text
GO only if /spiritflix/admin renders, can list/search/sort admin media records, can inspect details, and all admin APIs are read-only and root-contained.
```

## Level 2 - Guarded CRUD + Reorder

Level 2 adds write actions, but only with strict containment, previews, receipts, and reversible behavior where possible.

### Level 2 goals

Add safe media-management actions:

```text
create folder
rename file/folder
move file/folder
soft delete
restore from trash
edit SpiritFlix sidecar metadata
save custom order/reorder
trigger Jellyfin rescan
```

### Level 2 safety model

All write actions must go through a dedicated admin action API:

```text
src/app/api/spiritflix/admin/actions/route.ts
```

Every write action must use this flow:

```text
request
validate
preview
confirm
execute
receipt
refresh
```

No direct UI mutation without server validation.

Every action must return a receipt.

Suggested receipt path:

```text
/mnt/spirit-8tb/media/.spiritflix-admin-receipts/YYYYMMDD.jsonl
```

Receipt shape:

```ts
interface SpiritFlixAdminReceipt {
  id: string;
  timestamp: string;
  actor: "spiritflix-admin";
  action: string;
  status: "planned" | "executed" | "blocked" | "failed" | "rolled_back";
  sourcePath?: string;
  targetPath?: string;
  affectedPaths: string[];
  jellyfinItemIds?: string[];
  reason?: string;
  reversible: boolean;
  rollbackHint?: string;
}
```

### Level 2 write actions

#### 1. Create folder

Allow folder creation only under allowlisted media roots.

Validation:

```text
folder name sanitized
no path traversal
no overwrite
parent root allowed
receipt written
```

#### 2. Rename file/folder

Validation:

```text
source exists
source under allowed root
new name sanitized
target stays in same parent unless move action
target does not overwrite existing file
extension preserved by default for video files
receipt written
```

#### 3. Move file/folder

Validation:

```text
source exists
target parent exists
source and target under allowed roots
no overwrite
same filesystem preferred
large-folder move preview required
receipt written
```

#### 4. Soft delete

Do not hard delete in Level 2.

Move deleted items into:

```text
/mnt/spirit-8tb/media/.trash/YYYYMMDD/<original-relative-path>
```

Validation:

```text
source exists
source under allowed root
trash target unique
receipt written
restore path recorded
```

#### 5. Restore from trash

Allow restoring soft-deleted items if original target path is empty.

Validation:

```text
trash item exists
receipt exists or restore target explicitly selected
target does not overwrite
target under allowed root
receipt written
```

#### 6. Sidecar metadata edit

Allow editing SpiritFlix-owned sidecar metadata only, not raw Jellyfin database rows.

Possible sidecar path:

```text
/mnt/spirit-8tb/media/.spiritflix-admin/metadata/<hash>.json
```

Metadata fields:

```text
displayTitle
customTags
collection
notes
manualSortGroup
manualSortIndex
hiddenFromViewer
favoriteOverride
```

Do not edit Jellyfin DB directly.

#### 7. Custom ordering/reorder

Add drag-and-drop reorder for admin shelves/playlists.

Use existing installed drag/drop dependency if available.

Persist custom order to SpiritFlix sidecar JSON, not by renaming files.

Suggested file:

```text
/mnt/spirit-8tb/media/.spiritflix-admin/order.json
```

Suggested structure:

```ts
interface SpiritFlixAdminOrderFile {
  version: 1;
  updatedAt: string;
  groups: Array<{
    id: string;
    name: string;
    itemKeys: string[];
  }>;
}
```

Item keys should be stable:

```text
jellyfin:<itemId>
path:<sha256-normalized-path>
```

#### 8. Jellyfin rescan action

Add a guarded "request Jellyfin rescan" button.

Level 2 should support:

```text
preview rescan target
trigger full library scan or targeted refresh if available
show status/receipt
do not restart Jellyfin container
do not delete Jellyfin config
```

#### 9. Bulk actions

Level 2 may include basic bulk actions after single-item actions pass:

```text
bulk move
bulk soft delete
bulk add tag
bulk assign collection
```

Bulk actions must show count and affected paths before execution.

#### 10. Level 2 non-goals

Do not hard delete.
Do not expose public admin access.
Do not mutate Jellyfin SQLite DB directly.
Do not change Docker compose.
Do not wipe Jellyfin config.
Do not auto-download unauthorized media.
Do not bypass DRM.
Do not run destructive cleanup.
Do not rewrite the existing SpiritFlix player.
Do not collapse viewer and admin into one messy page.

## Suggested future implementation order

### Phase 0 - Audit and design doc only

This document is Phase 0.

No code implementation is approved by this document alone.

### Phase 1 - Level 1 read-only API

Future implementation should add:

```text
src/lib/spiritflix/admin/types.ts
src/lib/spiritflix/admin/paths.ts
src/lib/spiritflix/admin/fs.ts
src/lib/spiritflix/admin/jellyfin-admin.ts
src/app/api/spiritflix/admin/library/route.ts
src/app/api/spiritflix/admin/fs/route.ts
```

Add tests:

```text
src/lib/spiritflix/admin/__tests__/paths.test.ts
src/app/api/spiritflix/admin/__tests__/fs-route.test.ts
src/app/api/spiritflix/admin/__tests__/library-route.test.ts
```

### Phase 2 - Level 1 admin UI

Future implementation should add:

```text
src/app/spiritflix/admin/page.tsx
src/components/spiritflix/admin/SpiritFlixAdminApp.tsx
src/components/spiritflix/admin/SpiritFlixAdminExplorer.tsx
src/components/spiritflix/admin/SpiritFlixAdminTable.tsx
src/components/spiritflix/admin/SpiritFlixAdminToolbar.tsx
src/components/spiritflix/admin/SpiritFlixAdminDetailsPanel.tsx
```

Add a route link from SpiritFlix only if safe and not cluttered.

### Phase 3 - Level 1 verification

Future implementation should run:

```bash
npm run typecheck
vitest run src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
vitest run src/components/spiritflix/admin src/lib/spiritflix/admin src/app/api/spiritflix/admin
```

Manual smoke:

```text
open /spiritflix/admin
list libraries
sort by date added descending
search known video
open details panel
copy path
browse allowed folder
attempt ../ traversal and confirm blocked
```

### Phase 4 - Level 2 action API

Future implementation should add guarded action engine:

```text
src/lib/spiritflix/admin/actions.ts
src/lib/spiritflix/admin/receipts.ts
src/app/api/spiritflix/admin/actions/route.ts
```

Actions:

```text
createFolder
rename
move
softDelete
restore
writeMetadata
saveOrder
requestJellyfinRescan
```

All actions require preview and confirmation.

### Phase 5 - Level 2 UI controls

Future implementation should add admin UI controls:

```text
New folder
Rename
Move
Soft delete
Restore
Edit metadata
Save order
Rescan Jellyfin
```

No write button should execute until a preview has succeeded.

### Phase 6 - Level 2 verification

Add tests:

```text
path containment
folder create preview
rename preview
move preview
soft delete moves to trash path
restore rejects overwrite
sidecar write only under admin metadata root
order save validates stable item keys
receipt written for all actions
```

Manual smoke with disposable test folder only:

```text
/mnt/spirit-8tb/media/other/.spiritflix-admin-smoke/
```

Smoke sequence:

```text
create folder
rename folder
create nested folder
move disposable test file
soft delete disposable test file
restore disposable test file
save custom order
trigger rescan preview
confirm receipts exist
confirm no writes outside smoke folder except receipts/order metadata
```

## Final acceptance

Level 1 is accepted when:

```text
/spiritflix/admin exists
all media can be searched
videos can be sorted by date added
folders can be browsed
details are inspectable
paths can be copied
all APIs are read-only and path-safe
```

Level 2 is accepted when:

```text
admin can create folders
rename files/folders
move files/folders
soft delete and restore
save custom order
edit SpiritFlix sidecar metadata
request Jellyfin rescan
write receipts
block unsafe paths
avoid hard delete
avoid Jellyfin DB mutation
pass focused tests
```

## Next approval gate

After this document is written, stop.

Do not implement Level 1 or Level 2 until Britton approves a separate implementation prompt.
