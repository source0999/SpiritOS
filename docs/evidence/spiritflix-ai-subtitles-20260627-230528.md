# SpiritFlix AI Subtitles Evidence

- generatedAt: 2026-06-27T23:05:28.873810+00:00
- scope: file /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- model: base
- language: en
- backend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- media considered: 1
- ok: 0
- skipped: 0
- failed: 1

## Results

### Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4

- status: NO_GO
- mediaPath: /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- mediaKey: 7902d559989f124c188ca3b2
- selectedBackend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- selectedAudioStream: {'map': '0:2', 'index': 2, 'requested': None, 'detected': {'index': 2, 'codec_name': 'aac', 'codec_long_name': 'AAC (Advanced Audio Coding)', 'profile': 'LC', 'codec_type': 'audio', 'codec_tag_string': 'mp4a', 'codec_tag': '0x6134706d', 'sample_fmt': 'fltp', 'sample_rate': '48000', 'channels': 2, 'channel_layout': 'stereo', 'bits_per_sample': 0, 'initial_padding': 0, 'id': '0x3', 'r_frame_rate': '0/0', 'avg_frame_rate': '0/0', 'time_base': '1/48000', 'start_pts': 0, 'start_time': '0.000000', 'duration_ts': 66898944, 'duration': '1393.728000', 'bit_rate': '129328', 'nb_frames': '65332', 'extradata_size': 5, 'disposition': {'default': 0, 'dub': 0, 'original': 0, 'comment': 0, 'lyrics': 0, 'karaoke': 0, 'forced': 0, 'hearing_impaired': 0, 'visual_impaired': 0, 'clean_effects': 0, 'attached_pic': 0, 'timed_thumbnails': 0, 'non_diegetic': 0, 'captions': 0, 'descriptions': 0, 'metadata': 0, 'dependent': 0, 'still_image': 0}, 'tags': {'language': 'eng', 'handler_name': 'SoundHandler', 'vendor_id': '[0][0][0][0]'}}, 'reason': 'english_audio'}
- outputVttPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt
- manifestPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/7902d559989f124c188ca3b2.json
- qc: `null`
- skippedReason: AI_BACKEND_FAILED
- errors: `["Traceback (most recent call last):\n  File \"<string>\", line 12, in <module>\n  File \"/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/lib/python3.12/site-packages/faster_whisper/transcribe.py\", line 1851, in restore_speech_timestamps\n    for segment in segments:\n  File \"/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/lib/python3.12/site-packages/faster_whisper/transcribe.py\", line 1190, in generate_segments\n    encoder_output = self.encode(segment)\n                     ^^^^^^^^^^^^^^^^^^^^\n  File \"/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/lib/python3.12/site-packages/faster_whisper/transcribe.py\", line 1400, in encode\n    return self.model.encode(features, to_cpu=to_cpu)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nRuntimeError: Library libcublas.so.12 is not found or cannot be loaded\n"]`
