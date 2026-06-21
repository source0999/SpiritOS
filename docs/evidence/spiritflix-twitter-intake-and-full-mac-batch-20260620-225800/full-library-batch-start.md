# Full Library Batch

The full-library batch was not started by the intake script.

Start after tempTwitter is drained/stable and Britton gives GO:

```bash
node scripts/spiritflix-mobile-optimize.mjs --queue docs/evidence/spiritflix-phase7b-phase8-playback-order-20260620-211911/full-library-optimization-queue.csv --mac-host spirit-mac-mini --skip-existing --smallest-first --profile auto --workers 1 --stop-on-failure
```
