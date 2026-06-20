# S8.3 Baseline

Captured on the Dell host from `/home/source/SpiritOS`.

Raw baseline:

- `raw/00-baseline.txt`

Observed starting state:

- Current committed smart-tagging chain includes S7, S8, S8.1, and S8.2 through `a9ce0c2c`.
- The working tree already contained unrelated dirty files outside this task scope.
- Smart batch UI was readable after S8.2, but primary Smart Tags still showed technical/status tags such as `HD`, `mkv`, `long`, `unknown performer`, and `needs title cleanup`.
- Recommended names could display full filenames with `.mkv` or `.mp4` even though the operator view only needs the clean title/stem.
- Existing frame sampling writes frame evidence refs but does not classify visual scene/body/action content.
- Existing read-only performer data exists under `scripts/media/performer_verification.json` and `scripts/media/model_index.json`.
