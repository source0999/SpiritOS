# Next Batch Start Command

Do not run this until Britton gives GO after the live Fold/mobile test.

```bash
node scripts/spiritflix-mobile-optimize.mjs --queue docs/evidence/spiritflix-phase7b-phase8-playback-order-20260620-211911/full-library-optimization-queue.csv --mac-host spirit-mac-mini --skip-existing --smallest-first --profile auto --workers 1 --stop-on-failure
```

Notes:

- Queue count: 145
- Queue is sorted smallest-to-biggest.
- Source MP4s are preserved.
- Outputs are derivative MP4s with receipts.
- Dell should not perform heavy video optimization.
