# SpiritFlix Smart Naming Mini Context Pack

Date: 2026-06-20

## What This Is

SpiritFlix has a review-only smart tagging and naming flow for local media. It samples video frames, asks a local Ollama vision model for visual tags, writes sidecar analysis JSON, and shows pending tags/names in the admin batch review UI.

Nothing should auto-rename or auto-apply. Operators review tags and names first.

## Relevant Files

- `src/lib/spiritflix/admin/smart/visual-analysis.ts`
  - Runs local VLM frame analysis.
  - Filters banned/generic visual tags.
  - Has per-frame prompt and multi-frame video-level prompt.
  - Current default model: `gemma3n:e4b`.

- `src/lib/spiritflix/admin/smart/suggestions.ts`
  - Builds `suggestedDisplayTitle` / `suggestedFilename`.
  - Separates visible tag chips from title-worthy naming descriptors.
  - Preserves readable source titles.
  - Uses model folder numbering for random/spam filenames.

- `src/lib/spiritflix/admin/smart/sampler.ts`
  - Plans timestamps and extracts frame cache images.
  - Current frame cache version: `v2`.
  - Current extraction width: `768px`.

- `src/lib/spiritflix/admin/smart/vocabulary.ts`
  - Controlled tag list.
  - Recent additions: `hotel-room`, `threesome`, `traditional-dress`, `dress`, `smoking`.

- `src/lib/spiritflix/admin/smart/batch.ts`
  - Batch preview/run/review flow.
  - Computes model-folder sequence numbers.

- Main tests:
  - `src/lib/spiritflix/admin/smart/__tests__/visual-analysis.test.ts`
  - `src/lib/spiritflix/admin/smart/__tests__/suggestions.test.ts`
  - `src/lib/spiritflix/admin/smart/__tests__/sampler.test.ts`
  - `src/components/spiritflix/admin/__tests__/SpiritFlixSmartBatchPanel.test.tsx`

## Current Naming Rules

Readable source title:

```text
Model Name 02 - Readable Source Title
```

Random/spam filename with title-worthy visual descriptor:

```text
Model Name 03 - hotel room threesome
```

Random/spam filename with no reliable descriptor:

```text
Model Name 03 - Untitled
```

Unknown model fallback:

```text
Unknown Model - Untitled 01
```

## Important User Preference

The user does not want tag soup in names.

Bad:

```text
Aaliyah Yasan - curvy lingerie stockings 10
```

Preferred:

```text
Aaliyah Yasan 03 - hotel room threesome
Aaliyah Yasan 10 - traditional dress
```

Names should use:

- Performer/model identity when available.
- Model-folder sequence number when available.
- A short visual phrase only when frame evidence supports it.
- Existing readable source title when it is not random/spam.

## Tags The User Cares About

Useful visual tags include:

- Body/apparel/appearance: `curvy`, `busty`, `BBW`, `petite`, `slim`, `hijab`, `dress`, `traditional-dress`, `lingerie`, `stockings`, `tattoos`, `glasses`.
- Scene/activity/style: `hotel-room`, `threesome`, `smoking`, `toy`, `oral`, `manual`, `intercourse`, `anal`, `lesbian`, `massage`, `riding`, `missionary`, `doggy`, `standing`, `seated`, `cosplay`, `POV`, `watermark`.

Noise tags that should not appear as visible smart tags or title drivers:

- `solo`, `duo`, `group`, `indoor`, `outdoor`, `low-light`.
- Hair-color guesses like `brunette`, `black-hair`, `blonde`, `redhead`.
- Technical tags like `HD`, `mkv`, `long`, etc.

## Safety Boundary

Do not infer protected race, ethnicity, nationality, religion, or identity from appearance.

Visible clothing items can be tagged when actually visible. Example: `hijab` is allowed only if a visible head covering is clearly present, not from hair/shadow/identity guesses.

## Current Known Problem

The pipeline behavior is now conservative, but the installed local vision model is weak:

- It sometimes returns unparseable JSON.
- It has misread frames.
- It has copied prompt examples into observations.
- It overgeneralized the same tags across videos.

Recent fix gated free-text video-level observations so they do not become UI tag chips or names unless structured tag IDs are returned.

Final live proof from the last run:

- `HkkzMtwQexuQzwkQMekM.mkv` -> no visible tags, `Aaliyah Yasan 03 - Untitled`
- `Visit onlyshare.io for MORE 130.mkv` -> no visible tags, `Aaliyah Yasan 10 - Untitled`

This is safer than wrong tags, but not yet smart enough.

Evidence folder:

```text
docs/evidence/spiritflix-s9-frame-grounded-tags-names-20260620/
```

## Recent Commits

```text
e527563c fix: ground SpiritFlix smart tags in reliable frames
4ecfe59d fix: keep SpiritFlix smart tags relevant
bd9bca67 fix: suppress stale SpiritFlix solo indoor tags
dae7651d fix: enrich SpiritFlix visual tags and batch thumbnails
36695794 fix: use SpiritFlix model sequence names
```

## Best Next Direction For Another LLM

Do not hardcode video paths or per-file answers.

Focus on making the visual system genuinely frame-grounded:

1. Improve prompt/model output reliability so structured tags are returned consistently.
2. Add stronger frame quality/title-card filtering before VLM calls.
3. Consider a better local vision model if available; current `gemma3n:e4b` is the limiting factor.
4. Preserve conservative gating: wrong tags are worse than no tags.
5. Keep naming separate from tags:
   - Tags are many review chips.
   - Names use only a short, title-worthy phrase.

Validation target:

- For `HkkzMtwQexuQzwkQMekM.mkv`, desired shape is something like:

```text
Tags: hotel-room, threesome
Name: Aaliyah Yasan 03 - hotel room threesome
```

- For `Visit onlyshare.io for MORE 130.mkv`, desired shape is something like:

```text
Tags: traditional-dress or dress if frame evidence supports it
Name: Aaliyah Yasan 10 - traditional dress
```

Only produce those if the frame evidence actually supports them.
