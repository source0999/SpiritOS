# SpiritFlix AI Subtitles Evidence

- generatedAt: 2026-06-27T23:04:22.683709+00:00
- scope: file /mnt/spirit-8tb/media/yes/spiritos-test-video-2.mp4
- model: base
- language: en
- backend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- media considered: 1
- ok: 0
- skipped: 0
- failed: 1

## Results

### spiritos-test-video-2.mp4

- status: NO_GO
- mediaPath: /mnt/spirit-8tb/media/yes/spiritos-test-video-2.mp4
- mediaKey: 85b40b3b2da54b894fedcb78
- selectedBackend: {'name': 'faster-whisper', 'runner': 'python-module', 'python': '/mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python', 'path': None, 'installed': False}
- selectedAudioStream: {'map': '0:1', 'index': 1, 'requested': None, 'detected': {'index': 1, 'codec_name': 'aac', 'codec_long_name': 'AAC (Advanced Audio Coding)', 'profile': 'LC', 'codec_type': 'audio', 'codec_tag_string': 'mp4a', 'codec_tag': '0x6134706d', 'sample_fmt': 'fltp', 'sample_rate': '48000', 'channels': 1, 'channel_layout': 'mono', 'bits_per_sample': 0, 'initial_padding': 0, 'id': '0x2', 'r_frame_rate': '0/0', 'avg_frame_rate': '0/0', 'time_base': '1/48000', 'start_pts': 0, 'start_time': '0.000000', 'duration_ts': 480000, 'duration': '10.000000', 'bit_rate': '69213', 'nb_frames': '470', 'extradata_size': 5, 'disposition': {'default': 1, 'dub': 0, 'original': 0, 'comment': 0, 'lyrics': 0, 'karaoke': 0, 'forced': 0, 'hearing_impaired': 0, 'visual_impaired': 0, 'clean_effects': 0, 'attached_pic': 0, 'timed_thumbnails': 0, 'non_diegetic': 0, 'captions': 0, 'descriptions': 0, 'metadata': 0, 'dependent': 0, 'still_image': 0}, 'tags': {'language': 'und', 'handler_name': 'SoundHandler', 'vendor_id': '[0][0][0][0]'}}, 'reason': 'first_audio'}
- outputVttPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/85b40b3b2da54b894fedcb78/ai-en.vtt
- manifestPath: /mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/85b40b3b2da54b894fedcb78.json
- qc: `null`
- skippedReason: NO_CAPTION_SEGMENTS
- errors: `["AI backend returned no usable subtitle segments."]`
