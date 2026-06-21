# Phase 0 Safety Preflight

## pwd

Command: `pwd`

```
/home/source/SpiritOS
```

## hostname

Command: `hostname`

```
source-server
```

## date_is

Command: `date -Is`

```
2026-06-17T21:44:15-04:00
```

## git_status

Command: `git status --branch --short --untracked-files=normal`

```
## master
 M README.md
 M docs/media/spiritflix-smart-tagging-rename-plan.md
 M package-lock.json
 M package.json
 M repomix.config.json
 M scripts/media-ingest-worker.mjs
 M scripts/media/face_enrolled_performers.html
 M scripts/media/face_enrolled_performers.json
 M scripts/media/face_enrollment_queue.html
 M scripts/media/face_enrollment_queue.json
 M scripts/media/face_gallery.html
 M scripts/media/face_gallery.json
 M scripts/media/face_organizer.py
 M scripts/media/face_verification_full_audit.html
 M scripts/media/known_db_audit.html
 M scripts/media/known_db_audit.json
 M scripts/media/manual_crop.html
 M scripts/media/model_index.json
 M scripts/media/performer_verification.json
 M scripts/media/test_face_organizer_schema.py
 M scripts/runtime-port-guard.sh
 M scripts/source-context-compress.mjs
 M scripts/spiritos-lan-watchdog.sh
 M src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts
 M src/app/api/spiritflix/admin/smart/analysis/route.ts
 M src/app/layout.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx
 M src/lib/spiritflix/admin/smart/index.ts
 M src/lib/spiritflix/admin/smart/review.ts
 M src/lib/spiritflix/admin/smart/types.ts
 M src/styles/spiritflix.css
?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json
?? docs/evidence/source-proxy-glm-3x10-audit-20260617/
?? scripts/headroom-proxy-dev.sh
?? scripts/media/face_verification_report.json
?? scripts/postinstall-repomix-shim.mjs
?? scripts/repomix-llm.mjs
?? src/lib/spiritflix/admin/smart/__tests__/metadata-bridge.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/rename-preview.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts
?? src/lib/spiritflix/admin/smart/metadata-bridge.ts
?? src/lib/spiritflix/admin/smart/rename-preview.ts
?? src/lib/spiritflix/admin/smart/review-metadata.ts
```

## git_worktree

Command: `git worktree list`

```
/home/source/SpiritOS  158b489f [master]
```

## git_toplevel

Command: `git rev-parse --show-toplevel`

```
/home/source/SpiritOS
```

## git_head

Command: `git rev-parse HEAD`

```
158b489fcf813a701f8a7a1bf3f8be5770511448
```

## df_h

Command: `df -h`

```
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           1.6G   32M  1.6G   2% /run
efivarfs        256K  135K  117K  54% /sys/firmware/efi/efivars
/dev/sdb2       457G  281G  153G  65% /
tmpfs           7.8G     0  7.8G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/sda1       7.3T  156G  6.8T   3% /mnt/spirit-8tb
/dev/sdb1       1.1G  6.2M  1.1G   1% /boot/efi
tmpfs           1.6G  136K  1.6G   1% /run/user/1000
tmpfs           1.6G  104K  1.6G   1% /run/user/113
```

## free_h

Command: `free -h`

```
               total        used        free      shared  buff/cache   available
Mem:            15Gi       4.8Gi       7.2Gi       105Mi       3.9Gi        10Gi
Swap:          4.0Gi       878Mi       3.1Gi
```

## uptime

Command: `uptime`

```
 21:44:16 up 37 min,  6 users,  load average: 3.07, 2.58, 1.94
```

## who_b

Command: `who -b || true`

```
         system boot  2026-06-17 21:07
```

## last_x_head

Command: `last -x | head -80 || true`

```
runlevel (to lvl 5)   6.8.0-124-generi Wed Jun 17 21:11   still running
source   pts/0        100.82.31.124    Wed Jun 17 21:09   still logged in
reboot   system boot  6.8.0-124-generi Wed Jun 17 21:07   still running
source   pts/7        tmux(14286).%26  Wed Jun 17 06:03 - crash  (15:04)
source   pts/7        tmux(14286).%25  Wed Jun 17 05:51 - 06:03  (00:11)
source   pts/6        tmux(14286).%24  Wed Jun 17 05:45 - crash  (15:21)
source   pts/8        100.82.31.124    Wed Jun 17 05:41 - 20:59  (15:18)
source   pts/7        tmux(14286).%23  Tue Jun 16 20:51 - 05:51  (09:00)
source   pts/7        tmux(14286).%22  Tue Jun 16 20:14 - 20:51  (00:36)
source   pts/6        tmux(14286).%21  Tue Jun 16 20:08 - 05:45  (09:37)
source   pts/3        tmux(14286).%20  Tue Jun 16 19:49 - crash (1+01:17)
source   pts/5        tmux(14286).%19  Tue Jun 16 19:49 - crash (1+01:17)
source   pts/6        tmux(14286).%18  Tue Jun 16 19:48 - 20:08  (00:19)
source   pts/6        tmux(14286).%17  Tue Jun 16 19:17 - 19:48  (00:31)
source   pts/6        tmux(14286).%16  Tue Jun 16 19:10 - 19:17  (00:06)
source   pts/6        tmux(14286).%15  Tue Jun 16 19:06 - 19:10  (00:03)
source   pts/5        tmux(14286).%14  Tue Jun 16 19:06 - 19:49  (00:42)
source   pts/6        tmux(14286).%13  Tue Jun 16 19:01 - 19:05  (00:03)
source   pts/5        tmux(14286).%12  Tue Jun 16 19:01 - 19:06  (00:05)
source   pts/2        tmux(14286).%11  Tue Jun 16 16:13 - crash (1+04:54)
source   pts/6        tmux(14286).%10  Tue Jun 16 16:00 - 16:41  (00:40)
source   pts/2        tmux(14286).%9   Tue Jun 16 15:55 - 16:00  (00:05)
source   pts/2        tmux(14286).%8   Tue Jun 16 15:46 - 15:52  (00:05)
source   pts/2        tmux(14286).%7   Tue Jun 16 15:40 - 15:46  (00:05)
source   pts/2        tmux(14286).%6   Tue Jun 16 15:34 - 15:39  (00:05)
source   pts/5        tmux(14286).%5   Tue Jun 16 15:31 - 16:13  (00:41)
source   pts/2        tmux(14286).%4   Tue Jun 16 15:25 - 15:34  (00:09)
source   pts/2        tmux(14286).%3   Tue Jun 16 15:08 - 15:25  (00:16)
source   pts/4        tmux(14286).%2   Tue Jun 16 14:57 - 16:13  (01:15)
source   pts/3        tmux(14286).%1   Tue Jun 16 14:54 - 19:49  (04:54)
source   pts/2        tmux(14286).%0   Tue Jun 16 14:53 - 15:08  (00:14)
runlevel (to lvl 5)   6.8.0-124-generi Tue Jun 16 14:45 - 21:11 (1+06:26)
source   pts/0        100.82.31.124    Tue Jun 16 14:45 - 14:45  (00:00)
reboot   system boot  6.8.0-124-generi Tue Jun 16 14:41   still running
source   pts/3        tmux(15354).%226 Tue Jun 16 00:36 - 00:42  (00:05)
source   pts/1        tmux(15354).%225 Mon Jun 15 22:26 - crash  (16:15)
source   pts/7        tmux(15354).%224 Mon Jun 15 18:03 - crash  (20:37)
source   pts/6        tmux(15354).%223 Mon Jun 15 01:32 - crash (1+13:08)
source   pts/5        tmux(15354).%222 Mon Jun 15 01:03 - 00:33  (23:30)
source   pts/5        tmux(15354).%221 Mon Jun 15 00:28 - 01:02  (00:34)
source   pts/7        tmux(15354).%220 Sun Jun 14 23:20 - 23:21  (00:01)
source   pts/6        tmux(15354).%219 Sun Jun 14 23:20 - 00:14  (00:53)
source   pts/6        tmux(15354).%218 Sun Jun 14 23:16 - 23:16  (00:00)
source   pts/5        tmux(15354).%217 Sun Jun 14 23:06 - 00:15  (01:08)
source   pts/5        tmux(15354).%216 Sun Jun 14 23:04 - 23:04  (00:00)
source   pts/3        tmux(15354).%215 Sun Jun 14 22:48 - 22:25  (23:37)
source   pts/5        tmux(15354).%214 Sun Jun 14 20:56 - 22:48  (01:51)
source   pts/5        tmux(15354).%213 Sun Jun 14 16:32 - 18:01  (01:29)
source   pts/3        tmux(15354).%212 Sun Jun 14 16:32 - 20:56  (04:24)
source   pts/9        tmux(15354).%211 Sun Jun 14 12:36 - 13:41  (01:04)
source   pts/9        tmux(15354).%210 Sun Jun 14 12:36 - 12:36  (00:00)
source   pts/5        tmux(15354).%209 Sun Jun 14 12:35 - 16:32  (03:56)
source   pts/9        tmux(15354).%208 Sun Jun 14 11:43 - 12:19  (00:36)
source   pts/9        tmux(15354).%207 Sun Jun 14 11:31 - 11:36  (00:05)
source   pts/9        tmux(15354).%206 Sun Jun 14 11:30 - 11:31  (00:00)
source   pts/5        tmux(15354).%205 Sun Jun 14 11:30 - 12:35  (01:05)
source   pts/9        tmux(15354).%204 Sun Jun 14 10:35 - 11:12  (00:37)
source   pts/5        tmux(15354).%203 Sun Jun 14 10:34 - 11:29  (00:55)
source   pts/9        tmux(15354).%202 Sun Jun 14 10:06 - 10:34  (00:27)
source   pts/5        tmux(15354).%201 Sun Jun 14 09:27 - 10:34  (01:06)
source   pts/5        tmux(15354).%200 Sun Jun 14 09:27 - 09:27  (00:00)
source   pts/5        tmux(15354).%199 Sun Jun 14 09:27 - 09:27  (00:00)
source   pts/9        tmux(15354).%198 Sun Jun 14 08:17 - 09:26  (01:08)
source   pts/5        tmux(15354).%197 Sun Jun 14 08:10 - 08:17  (00:06)
source   pts/5        tmux(15354).%196 Sun Jun 14 08:00 - 08:10  (00:09)
source   pts/9        tmux(15354).%195 Sun Jun 14 07:49 - 08:00  (00:10)
source   pts/9        tmux(15354).%194 Sun Jun 14 07:35 - 07:49  (00:13)
source   pts/5        tmux(15354).%193 Sun Jun 14 07:33 - 07:54  (00:20)
source   pts/9        tmux(15354).%192 Sun Jun 14 07:28 - 07:35  (00:07)
source   pts/5        tmux(15354).%191 Sun Jun 14 07:24 - 07:33  (00:09)
source   pts/9        tmux(15354).%190 Sun Jun 14 07:16 - 07:28  (00:11)
source   pts/5        tmux(15354).%189 Sun Jun 14 07:14 - 07:16  (00:02)
source   pts/10       tmux(15354).%188 Sun Jun 14 07:12 - 07:24  (00:12)
source   pts/9        tmux(15354).%187 Sun Jun 14 07:03 - 07:12  (00:08)
source   pts/5        tmux(15354).%186 Sun Jun 14 06:59 - 07:14  (00:14)
source   pts/10       tmux(15354).%185 Sun Jun 14 06:53 - 06:59  (00:05)
source   pts/5        tmux(15354).%184 Sun Jun 14 06:53 - 06:53  (00:00)
source   pts/2        tmux(15354).%183 Sat Jun 13 23:42 - crash (2+14:58)
source   pts/9        tmux(15354).%182 Sat Jun 13 23:39 - 07:03  (07:24)
source   pts/5        tmux(15354).%181 Sat Jun 13 23:36 - 23:39  (00:02)
```
