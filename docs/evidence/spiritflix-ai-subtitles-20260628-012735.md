# SpiritFlix AI Subtitles Evidence

- generatedAt: 2026-06-28T01:27:35.452417+00:00
- scope: file /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- model: base
- language: en
- backend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- timingConfig: `{"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}`
- preferEmbeddedEnglish: False
- media considered: 1
- ok: 1
- skipped: 0
- failed: 0

## Results

### Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4

- status: ok
- mediaPath: /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- mediaKey: 7902d559989f124c188ca3b2
- selectedBackend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- selectedAudioStream: {'map': '0:2', 'index': 2, 'requested': None, 'detected': {'index': 2, 'codec_name': 'aac', 'codec_long_name': 'AAC (Advanced Audio Coding)', 'profile': 'LC', 'codec_type': 'audio', 'codec_tag_string': 'mp4a', 'codec_tag': '0x6134706d', 'sample_fmt': 'fltp', 'sample_rate': '48000', 'channels': 2, 'channel_layout': 'stereo', 'bits_per_sample': 0, 'initial_padding': 0, 'id': '0x3', 'r_frame_rate': '0/0', 'avg_frame_rate': '0/0', 'time_base': '1/48000', 'start_pts': 0, 'start_time': '0.000000', 'duration_ts': 66898944, 'duration': '1393.728000', 'bit_rate': '129328', 'nb_frames': '65332', 'extradata_size': 5, 'disposition': {'default': 0, 'dub': 0, 'original': 0, 'comment': 0, 'lyrics': 0, 'karaoke': 0, 'forced': 0, 'hearing_impaired': 0, 'visual_impaired': 0, 'clean_effects': 0, 'attached_pic': 0, 'timed_thumbnails': 0, 'non_diegetic': 0, 'captions': 0, 'descriptions': 0, 'metadata': 0, 'dependent': 0, 'still_image': 0}, 'tags': {'language': 'eng', 'handler_name': 'SoundHandler', 'vendor_id': '[0][0][0][0]'}}, 'reason': 'english_audio'}
- provenance: ai-asr-word-timed
- wordTimestampsUsed: True
- englishDubAudioSource: True
- outputVttPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt
- manifestPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/7902d559989f124c188ca3b2.json
- baselineExistingQc: `{"averageCueDurationSeconds": 2.783, "averageCueGapSeconds": 2.327, "cueCount": 246, "cueGapCount": 245, "cuesWithoutDetectedSpeechOverlapCount": 3, "emptyCueCount": 0, "endsAfterDetectedSpeechCount": 0, "englishDubAudioSource": true, "fileSizeBytes": 20410, "firstCueTime": "00:02:19.310", "lastCueTime": "00:23:13.990", "longCueCount": 0, "longCueGapCount": 67, "longSilenceLingerViolationCount": 0, "maxCueDurationSeconds": 6.0, "maxCueGapSeconds": 103.27, "overlapCount": 0, "provenance": "ai-asr-segment-timed", "speechCompared": true, "startsBeforeDetectedSpeechCount": 0, "startsWithWebVtt": true, "suspiciouslyEarlyStartPercent": 0.0, "timingConfig": {"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}, "totalCaptionedDurationSeconds": 684.557, "wordTimestampsUsed": false, "zeroDurationCueCount": 0}`
- rawQc: `{"averageCueDurationSeconds": 3.869, "averageCueGapSeconds": 2.89, "cueCount": 186, "cueGapCount": 185, "cuesWithoutDetectedSpeechOverlapCount": 0, "emptyCueCount": 0, "endsAfterDetectedSpeechCount": 1, "englishDubAudioSource": true, "fileSizeBytes": 0, "firstCueTime": "00:02:19.310", "lastCueTime": "00:23:13.640", "longCueCount": 27, "longCueGapCount": 76, "longSilenceLingerViolationCount": 17, "maxCueDurationSeconds": 29.37, "maxCueGapSeconds": 103.62, "overlapCount": 0, "provenance": "ai-asr-word-timed", "speechCompared": true, "startsBeforeDetectedSpeechCount": 17, "startsWithWebVtt": true, "suspiciouslyEarlyStartPercent": 9.14, "timingConfig": {"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}, "totalCaptionedDurationSeconds": 719.69, "wordTimestampsUsed": true, "zeroDurationCueCount": 0}`
- repair: `{"emptyOrJunkCueRemovedCount": 0, "endClampedCount": 21, "inputCueCount": 186, "noSpeechCueDroppedCount": 3, "outputCueCount": 243, "overlapAdjustedCount": 80, "segmentFallbackInputCueCount": 0, "splitCueCount": 46, "startClampedCount": 26, "timingMode": "word_vad_clamp", "wordTimedInputCueCount": 186}`
- qc: `{"averageCueDurationSeconds": 2.815, "averageCueGapSeconds": 2.358, "cueCount": 243, "cueGapCount": 242, "cuesWithoutDetectedSpeechOverlapCount": 0, "emptyCueCount": 0, "endsAfterDetectedSpeechCount": 0, "englishDubAudioSource": true, "fileSizeBytes": 20258, "firstCueTime": "00:02:19.310", "lastCueTime": "00:23:13.990", "longCueCount": 0, "longCueGapCount": 67, "longSilenceLingerViolationCount": 0, "maxCueDurationSeconds": 6.0, "maxCueGapSeconds": 103.27, "overlapCount": 0, "provenance": "ai-asr-word-timed", "speechCompared": true, "startsBeforeDetectedSpeechCount": 0, "startsWithWebVtt": true, "suspiciouslyEarlyStartPercent": 0.0, "timingConfig": {"globalOffsetMs": 0, "maxCueMs": 6000, "maxLeadMs": 150, "maxLineChars": 42, "maxLingerMs": 350, "minCueMs": 600, "silenceNoiseDb": -35, "splitSilenceMs": 700, "timingMode": "word_vad_clamp"}, "totalCaptionedDurationSeconds": 684.093, "wordTimestampsUsed": true, "zeroDurationCueCount": 0}`
- selectedCaptionTrack: `null`
- skippedReason: None
- errors: `[]`

#### Before/After Sample

- before:
  - 00:02:19.310 --> 00:02:24.890: If the stab misses, I can change it into a side sweeping attack without pause. There is no weakness
  - 00:02:24.890 --> 00:02:30.470: in the Hirazuki attack that was developed by Toshizohijigata, assistant leader of the Shinsengumi,
  - 00:02:30.790 --> 00:02:56.990: especially my variation of it. There's a Totsu, a Totsu, numerous times between the revolution
  - 00:02:56.990 --> 00:03:02.130: and the Meiji era combined with my Totsu technique. There's no way you could hope to defeat
  - 00:03:02.130 --> 00:03:06.010: me as you are now. This guy is in a completely different class.
  - 00:03:06.010 --> 00:03:35.380: He has a deep wound in his chest area. His response to my second attack was faster than
  - 00:03:35.380 --> 00:03:41.680: the first. It's as I expected. Each time he swings his sword, he is gradually, unconsciously
  - 00:03:41.680 --> 00:03:49.900: but surely returning to his former self. But Tosai, the manslayer, let's go. He's
  - 00:03:49.900 --> 00:04:08.380: not even faster. What was that? That move far surpassed my expectations. His breathing,
  - 00:04:08.380 --> 00:04:13.160: He's using more strength than he thinks he has, and his body can't keep up.
- after:
  - 00:02:19.310 --> 00:02:25.240: If the stab misses, I can change it into a side sweeping attack without pause. There is no weakness
  - 00:02:25.240 --> 00:02:30.820: in the Hirazuki attack that was developed by Toshizohijigata, assistant leader of the Shinsengumi,
  - 00:02:30.820 --> 00:02:35.200: especially my variation of it. There's Totsu,
  - 00:02:36.960 --> 00:02:37.830: a Totsu,
  - 00:02:55.490 --> 00:02:57.340: numerous times between the revolution
  - 00:02:57.340 --> 00:03:02.480: and the Meiji era combined with my Totsu technique. There's no way you could hope to defeat
  - 00:03:02.480 --> 00:03:06.360: me as you are now. This guy is in a completely different class.
  - 00:03:06.360 --> 00:03:06.960: He
  - 00:03:30.960 --> 00:03:35.730: has a deep wound in his chest area. His response to my second attack was faster than
  - 00:03:35.730 --> 00:03:36.170: the first.
