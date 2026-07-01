# SpiritFlix AI Subtitles Evidence

- generatedAt: 2026-06-28T01:28:16.280561+00:00
- scope: file /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- model: base
- language: en
- backend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- timingConfig: `{"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}`
- preferEmbeddedEnglish: True
- media considered: 1
- ok: 0
- skipped: 1
- failed: 0

## Results

### Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4

- status: skipped
- mediaPath: /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- mediaKey: 7902d559989f124c188ca3b2
- selectedBackend: None
- selectedAudioStream: None
- provenance: embedded-extracted
- wordTimestampsUsed: None
- englishDubAudioSource: None
- outputVttPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt
- manifestPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/7902d559989f124c188ca3b2.json
- baselineExistingQc: `null`
- rawQc: `null`
- repair: `null`
- qc: `{"averageCueDurationSeconds": 2.55, "averageCueGapSeconds": 1.406, "cueCount": 355, "cueGapCount": 354, "cuesWithoutDetectedSpeechOverlapCount": 0, "emptyCueCount": 0, "endsAfterDetectedSpeechCount": 0, "englishDubAudioSource": true, "fileSizeBytes": 21969, "firstCueTime": "00:00:11.530", "lastCueTime": "00:23:34.520", "longCueCount": 8, "longCueGapCount": 100, "longSilenceLingerViolationCount": 0, "maxCueDurationSeconds": 8.12, "maxCueGapSeconds": 40.82, "overlapCount": 0, "provenance": "embedded-extracted", "speechCompared": false, "startsBeforeDetectedSpeechCount": 0, "startsWithWebVtt": true, "suspiciouslyEarlyStartPercent": 0.0, "timingConfig": {"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}, "totalCaptionedDurationSeconds": 905.32, "wordTimestampsUsed": false, "zeroDurationCueCount": 0}`
- selectedCaptionTrack: `{"cachePath": "/mnt/spirit-8tb/media/.spiritflix-admin/captions/cache/7902d559989f124c188ca3b2/caption-282894e9d081f31c.vtt", "default": true, "forced": false, "id": "caption-282894e9d081f31c", "kind": "subtitles", "label": "SubtitleHandler", "language": "eng", "outputFormat": "vtt", "publicUrl": "/api/spiritflix/captions/file?key=7902d559989f124c188ca3b2&track=caption-282894e9d081f31c", "reviewStatus": "source", "sdh": false, "sourceFormat": "mov_text", "sourcePath": null, "sourceType": "embedded", "streamIndex": 3}`
- skippedReason: preferred_embedded_english_source
- errors: `[]`
