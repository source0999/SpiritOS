# SpiritFlix AI Subtitle Refinement Closeout

- generatedAt: 2026-06-28T01:32:00Z
- pilot media: `/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4`
- mediaKey: `7902d559989f124c188ca3b2`
- backend: `faster-whisper/base`
- selected ASR audio: `0:2`, language `eng`, reason `english_audio`
- final AI provenance: `ai-asr-word-timed`
- default source preference: `embedded-extracted` full English source track

## Audit

- Generation path: `scripts/media/spiritflix_ai_subtitles.py`
- Inventory path: `scripts/media/spiritflix_caption_inventory.py`
- Extraction path: `scripts/media/spiritflix_caption_extract.py`
- Older guarded one-file generator: `scripts/media/spiritflix_caption_generate_ai.py`
- Serving routes: `src/app/api/spiritflix/captions/manifest/route.ts` and `src/app/api/spiritflix/captions/file/route.ts`
- Manifest reader: `src/lib/spiritflix/captions.ts`
- Player consumer: `src/components/spiritflix/SpiritFlixPlayer.tsx`
- VTT output: `/mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/{mediaKey}/ai-en.vtt`
- Manifest output: `/mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/{mediaKey}.json`

Before this pass, `faster-whisper` used `vad_filter=True` but emitted only segment-level subtitles into the VTT. Cue cleanup was basic: junk text removal, overlap prevention, and zero-duration checks. It did not retain word timestamps, did not compare cues against detected speech, did not split long silence inside a segment, and did not skip AI generation when a full embedded English subtitle track already existed.

## Patch

- Added config-backed timing controls: `AI_SUBTITLE_TIMING_MODE`, `AI_SUBTITLE_MAX_LEAD_MS`, `AI_SUBTITLE_MAX_LINGER_MS`, `AI_SUBTITLE_SPLIT_SILENCE_MS`, `AI_SUBTITLE_MIN_CUE_MS`, `AI_SUBTITLE_MAX_CUE_MS`, `AI_SUBTITLE_PREFER_EMBEDDED_ENGLISH`.
- Added word timestamp capture for `faster-whisper` and Python `whisper` when available.
- Added verbatim English-dub ASR prompt/options and disabled previous-text conditioning for local Whisper paths.
- Added `ffmpeg` `silencedetect` speech-span QC and repair.
- Added repair pass that splits word-timed cues on long gaps, clamps starts to speech onset, clamps ends before silence linger, drops no-speech fragments, prevents overlaps, wraps long lines, and preserves sane cue duration.
- Added QC-only verifier mode: `--verify-vtt`.
- Added default full embedded English source preference; AI can still be forced with `--no-prefer-embedded-english` for repair testing.
- Added manifest metadata: `provenance`, `timingMode`, `wordTimestampsUsed`, and `englishDubAudioSource`.

## Commands

- `python -m py_compile scripts\media\spiritflix_ai_subtitles.py`
- `python3 -m py_compile scripts/media/spiritflix_ai_subtitles.py`
- `python3 scripts/media/spiritflix_ai_subtitles.py --detect-only --no-install`
- `python3 scripts/media/spiritflix_ai_subtitles.py --file ...S02E03... --model base --language en --no-install --force`
- `python3 scripts/media/spiritflix_ai_subtitles.py --file ...S02E03... --verify-vtt /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt --language en --no-install`
- `python3 scripts/media/spiritflix_ai_subtitles.py --file ...S02E03... --model base --language en --no-install --force --no-prefer-embedded-english`
- `git diff --check -- scripts/media/spiritflix_ai_subtitles.py`

## Metrics

| Metric | Old generated AI VTT | Raw word-timed ASR | Final repaired AI VTT |
|---|---:|---:|---:|
| cueCount | 238 | 186 | 243 |
| averageCueDurationSeconds | 5.166 | 3.869 | 2.815 |
| maxCueDurationSeconds | 100.51 | 29.37 | 6.0 |
| longCueCount | 33 | 27 | 0 |
| startsBeforeDetectedSpeechCount | 20 | 17 | 0 |
| suspiciouslyEarlyStartPercent | 8.4 | 9.14 | 0.0 |
| endsAfterDetectedSpeechCount | 13 | 1 | 0 |
| longSilenceLingerViolationCount | 40 | 17 | 0 |
| cuesWithoutDetectedSpeechOverlapCount | 0 | 0 | 0 |
| overlapCount | 0 | 0 | 0 |
| totalCaptionedDurationSeconds | 1229.62 | 719.69 | 684.093 |
| wordTimestampsUsed | false | true | true |
| englishDubAudioSource | true | true | true |

Standalone final verifier evidence:

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/caption-qc/caption-qc-20260628-012800-7902d559989f124c188ca3b2.json`

Generation evidence:

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/ai-subtitles/ai-subtitles-20260628-012735-7902d559989f124c188ca3b2.json`
- `docs/evidence/spiritflix-ai-subtitles-20260628-012735.md`

Embedded-source preference evidence:

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/ai-subtitles/ai-subtitles-20260628-012816-7902d559989f124c188ca3b2.json`
- `docs/evidence/spiritflix-ai-subtitles-20260628-012816.md`

## Cue Samples

Before repair:

- `00:02:30.790 --> 00:02:56.990`: `especially my variation of it. There's a Totsu, a Totsu, numerous times between the revolution`
- `00:03:06.010 --> 00:03:35.380`: `He has a deep wound in his chest area. His response to my second attack was faster than`
- `00:03:49.900 --> 00:04:08.380`: `not even faster. What was that? That move far surpassed my expectations. His breathing,`

After repair:

- `00:02:30.820 --> 00:02:35.200`: `especially my variation of it. There's Totsu,`
- `00:02:36.960 --> 00:02:37.830`: `a Totsu,`
- `00:02:55.490 --> 00:02:57.340`: `numerous times between the revolution`
- `00:03:30.960 --> 00:03:35.730`: `has a deep wound in his chest area. His response to my second attack was faster than`
- `00:04:00.600 --> 00:04:01.650`: `What was that?`

## Regenerated Files

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt`
- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/7902d559989f124c188ca3b2.json`
- AI generation and QC receipts under `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/`
- `docs/evidence/spiritflix-ai-subtitles-20260628-012735.md`
- `docs/evidence/spiritflix-ai-subtitles-20260628-012816.md`

## Known Limits

- Exact dub wording is still not guaranteed by `faster-whisper/base`. The forced AI sample still mishears some names/phrases.
- For this pilot, production/default behavior is better than AI because a full embedded English track exists and is preferred.
- For files without embedded English subtitles, timing/linger is now speech-checked and word-timed when the backend supports it, but wording accuracy would improve most with a larger local model such as `medium`/`large-v3` or a dedicated alignment backend.

## Verdict

PARTIAL. Timing and linger are fixed with verifier proof for the pilot AI path, and embedded English subtitles are preferred by default. The remaining limit is exact ASR wording when no embedded English subtitle track exists.
