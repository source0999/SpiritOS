# Model Storage Audit

Verdict: **PARTIAL-GO**

## Path and Disk Checks

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb2       457G  281G  153G  65% /
/dev/sda1       7.3T  156G  6.8T   3% /mnt/spirit-8tb
```

```
NAME   FSTYPE FSVER LABEL      UUID                                 FSAVAIL FSUSE% MOUNTPOINTS
sda
└─sda1 ext4   1.0   spirit-8tb 89266aec-4ec8-4aa8-bf4b-dd08e8699ed3    6.7T     2% /mnt/storage8tb
                                                                                   /mnt/spirit-8tb
sdb
├─sdb1 vfat   FAT32            45B7-F176                                 1G     1% /boot/efi
└─sdb2 ext4   1.0              fa1fa908-2de6-4c7f-b844-e53bdc22002c  152.3G    62% /mnt/spirit-8tb/media/yes
                                                                                   /
```

```
/dev/sda1 on /mnt/spirit-8tb type ext4 (rw,relatime)
/dev/sdb2 on /mnt/spirit-8tb/media/yes type ext4 (rw,relatime)
/dev/sda1 on /mnt/storage8tb type ext4 (rw,relatime)
```

## Ollama Path Resolution

`/usr/share/ollama/.ollama` resolves to:

```
/mnt/spirit-8tb/ollama-models
```

`/usr/share/ollama/.ollama/models` resolves to:

```
/mnt/spirit-8tb/ollama-models/models
```

## Size Checks

```
0	/usr/share/ollama/.ollama
```

```
88K	/mnt/spirit-8tb/ollama-models/models/manifests
34G	/mnt/spirit-8tb/ollama-models
34G	/mnt/spirit-8tb/ollama-models/models
34G	/mnt/spirit-8tb/ollama-models/models/blobs
```

## Runtime Configuration

```
MainPID=1448
Environment=PATH=/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
User=ollama
FragmentPath=/etc/systemd/system/ollama.service
DropInPaths=
```

```
# /etc/systemd/system/ollama.service
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"

[Install]
WantedBy=default.target
```

## Runtime / Model List

```
NAME                                                     ID              SIZE      MODIFIED
gemma3n:e4b                                              15cb39fd9394    7.5 GB    7 days ago
hermes4:latest                                           3e79497c9643    9.0 GB    2 weeks ago
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M    ce5cb56a7898    9.0 GB    2 weeks ago
hermes3:8b-abliterated                                   621eb9c2e65e    4.7 GB    3 weeks ago
mannix/llama3-8b-ablitered-v3:latest                     46688a22037e    4.7 GB    3 weeks ago
qwen2.5-coder:7b                                         dae161e27b0e    4.7 GB    4 weeks ago
llama3.1:8b                                              46e0c10c039e    4.9 GB    4 weeks ago
llama3:latest                                            365c0bd3c000    4.7 GB    2 months ago
```

```
ollama      1448  0.0  0.1 2160960 21212 ?       Ssl  21:08   0:00 /usr/local/bin/ollama serve
```

## Permission Checks

Read check:

```
sudo: a password is required
```

Write check:

```
sudo: a password is required
```


## Auditor Synthesis

- `/usr/share/ollama/.ollama` resolves to `/mnt/spirit-8tb/ollama-models`.
- `/usr/share/ollama/.ollama/models` resolves to `/mnt/spirit-8tb/ollama-models/models`.
- The 8TB mount is `/dev/sda1`, size `7.3T`, with `6.8T` available; root `/` is `/dev/sdb2`, size `457G`, with `153G` available.
- The model tree under `/mnt/spirit-8tb/ollama-models` is about `34G` and `ollama list` returns installed models.
- Verdict remains `PARTIAL-GO`, not `GO`, only because passwordless sudo was unavailable for `sudo -u ollama` read/write proof. The path and runtime evidence strongly indicate model storage is on the 8TB drive.
