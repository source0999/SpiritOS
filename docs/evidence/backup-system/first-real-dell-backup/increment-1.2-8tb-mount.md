# Increment 1.2 8TB Mount

Date: 2026-05-29

Checks run:

- `findmnt /mnt/spirit-8tb`: PASS
- `df -h /mnt/spirit-8tb`: PASS
- `ls -ld /mnt/spirit-8tb`: PASS

Observed:

```text
TARGET          SOURCE    FSTYPE OPTIONS
/mnt/spirit-8tb /dev/sda1 ext4   rw,relatime
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       7.3T   28K  6.9T   1% /mnt/spirit-8tb
drwxr-xr-x 3 root root 4096 May 28 21:02 /mnt/spirit-8tb
```

Result: GO. The 8TB drive is mounted and has enough free space. The mount is root-owned, so approved directory creation may require `sudo`.
