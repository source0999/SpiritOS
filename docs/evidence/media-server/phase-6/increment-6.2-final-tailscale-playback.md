# Increment 6.2 Final Tailscale Playback

Purpose:

- Prove playback from another Tailscale device.

Terminal-safe route verification:

```bash
curl -I --max-time 8 http://spirit.tailb69ea6.ts.net:8096
curl -I --max-time 8 http://100.111.32.31:8096
```

Terminal-safe output:

```text
http://spirit.tailb69ea6.ts.net:8096 -> HTTP/1.1 302 Found, Location: web/
http://100.111.32.31:8096 -> HTTP/1.1 302 Found, Location: web/
```

User manual check:

```text
USER_MANUAL_CHECK_PENDING
1. From another Tailscale device, open http://spirit.tailb69ea6.ts.net:8096.
2. Log in.
3. Open Home Videos and Photos.
4. If needed, run or wait for Scan All Libraries.
5. Start playback for one of the 2024-07-23 MP4 files.
6. Confirm video/audio starts.
```

Status: PARTIAL-GO_USER_MANUAL_CHECK_PENDING
