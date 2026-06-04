# Playback Tuning VAAPI

Purpose:

- Improve Jellyfin playback startup/transcoding performance on the Dell without public exposure or moving media.

Problem reported:

- Shuffle inside a folder reported a playback error: unable to find a valid media source.
- Video loading was slow.
- User asked whether to use a Mac pre-transcode workflow or Dell acceleration.

Decision:

- Enable Dell-side hardware acceleration first.
- Use Intel VAAPI on `/dev/dri/renderD128` because Jellyfin runs on the Dell where the media is stored.
- Keep Mac pre-transcode as a later optional workflow for optimized copies if Dell acceleration is not enough.

Compose change:

```yaml
devices:
  - /dev/dri:/dev/dri
group_add:
  - "44"
  - "993"
```

Jellyfin encoding config change:

```text
HardwareAccelerationType: vaapi
VaapiDevice: /dev/dri/renderD128
EnableHardwareEncoding: true
```

Backup:

```text
/mnt/spirit-8tb/services/jellyfin/config/config/encoding.xml.before-vaapi-latest
```

Verification:

```text
Jellyfin container sees /dev/dri.
Jellyfin logs: VAAPI device /dev/dri/renderD128 is Intel GPU (iHD).
Jellyfin logs list available hwaccel types including vaapi and qsv.
Jellyfin container is running healthy after restart.
Local HTTP responds with HTTP/1.1 302 Found.
```

Notes:

- NVIDIA runtime exists, but the RTX 3060 was mostly occupied by Ollama during inspection, so Intel VAAPI is the cleaner first path.
- Existing Tailscale/public exposure settings were not changed.
- No SpiritOS media UI, YTMClone, `.env`, or production Compose file was edited.

Next user check:

- Retry playback.
- If direct play is still slow, lower playback quality in the Jellyfin client to force transcoding and confirm it starts faster.
- If shuffle still errors, run Scan All Libraries and test one individual video before testing shuffle again.
