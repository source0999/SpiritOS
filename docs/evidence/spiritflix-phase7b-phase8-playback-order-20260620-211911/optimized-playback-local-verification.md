# Optimized Playback Local Verification

## Phase 7 Output Checked

Example optimized receipt/output:

- Receipt: `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/20260621/phase7-candidate-09.json`
- Source: `/mnt/spirit-8tb/media/yes/RisqueCore Vid 10.mp4`
- Output: `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/20260621/phase7-candidate-09.mp4`
- Receipt status: `ok`
- Output exists: yes
- Profile: `mobile-720p`

## Local Verification Results

- Optimized receipt exists: yes
- Optimized output exists: yes
- Source selection chooses Mac optimized MP4 in component test: yes
- Diagnostics show `mac_optimized_mp4` in component test: yes
- Range requests work in API route test: yes
- HLS starts as fallback only: yes
- No new Dell ffmpeg started from verification: yes
- Live YES is MP4-only: yes
- Old Dell MKV worker disabled/stopped: yes

Live Fold/mobile proof was intentionally not claimed in this task.
