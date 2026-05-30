# Increment 1.1.4 Node Inventory

Date: 2026-05-29

Dell/source-server:

- Repo path expected: `/home/source/SpiritOS`
- 8TB mount expected around `/mnt/spirit-8tb`
- Mount and capacity are checked with `findmnt /mnt/spirit-8tb` and `df -h /mnt/spirit-8tb`

Mac mini support node:

- SSH alias expected: `spirit-mac-mini`
- Worker checkout expected: `/Users/spiritmac/spiritos-worker/SpiritOS`
- Check is reachability and path presence only.
- No Mac data is copied and no Mac secrets are read.

Windows desktop node:

- Scope expected to center around `C:\Projects`
- Existing config references are discovered from examples/docs/scripts/source only.
- No token or credential is required.

Manual checks to rerun:

```bash
cd /home/source/SpiritOS
hostname
findmnt /mnt/spirit-8tb || true
df -h /mnt/spirit-8tb || true
ssh -o BatchMode=yes -o ConnectTimeout=5 spirit-mac-mini 'hostname; whoami; test -d /Users/spiritmac/spiritos-worker/SpiritOS && echo MAC_SPIRITOS_PATH_PRESENT || echo MAC_SPIRITOS_PATH_MISSING' 2>/dev/null || true
grep -R "SPIRITDESKTOP_TELEMETRY_URL\|SPIRIT_WINDOWS_FS_ALLOWLIST\|C:\\\\Projects" -n .env.local.example docs scripts src 2>/dev/null | head -80 || true
git diff --check
```
