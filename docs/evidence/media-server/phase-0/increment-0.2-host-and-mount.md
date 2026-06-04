# Increment 0.2 Host And Mount Baseline

Status: GO

Command:

```bash
hostname
whoami
pwd
findmnt /mnt/spirit-8tb
df -h /mnt/spirit-8tb
ls -ld /mnt/spirit-8tb
```

Output:

```text
source-server
source
/home/source
TARGET          SOURCE    FSTYPE OPTIONS
/mnt/spirit-8tb /dev/sda1 ext4   rw,relatime
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       7.3T   60G  6.8T   1% /mnt/spirit-8tb
drwxr-xr-x 11 root root 4096 Jun  1 20:05 /mnt/spirit-8tb
```

Manual check:

- Host is the Dell/source server: `source-server`.
- Executor user is `source`.
- `/mnt/spirit-8tb` is mounted as ext4 from `/dev/sda1`.
- 8 TB drive has 6.8T available.
- No writes were made under `/mnt/spirit-8tb`.

Rollback:

- Documentation-only. If this host or mount is wrong, stop before Phase 1.
