# Increment 1.1 - Ollama 8TB model path

Date: 2026-05-29T19:52:24-04:00

```text
=== ollama service ===
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
Environment=PATH=/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/home/source/.cursor-server/bin/linux-x64/3a67af7b780e0bfc8d32aefa96b8ff1cb8817f80/bin/remote-cli:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
FragmentPath=/etc/systemd/system/ollama.service
DropInPaths=
=== model path checks ===
TARGET          SOURCE    FSTYPE OPTIONS
/mnt/spirit-8tb /dev/sda1 ext4   rw,relatime
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       7.3T   28G  6.9T   1% /mnt/spirit-8tb
drwxr-xr-x 3 source source 4096 May 29 19:34 /mnt/spirit-8tb/models
drwxr-xr-x 3 ollama ollama 4096 Apr 16 22:54 /mnt/spirit-8tb/ollama-models
lrwxrwxrwx 1 ollama ollama 29 May 29 19:31 /usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models
/mnt/spirit-8tb/ollama-models
=== ollama env process check ===
=== models visible ===
NAME                                                     ID              SIZE      MODIFIED      
hermes4:latest                                           3e79497c9643    9.0 GB    5 minutes ago    
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M    ce5cb56a7898    9.0 GB    6 minutes ago    
hermes3:8b-abliterated                                   621eb9c2e65e    4.7 GB    4 days ago       
mannix/llama3-8b-ablitered-v3:latest                     46688a22037e    4.7 GB    4 days ago       
qwen2.5-coder:7b                                         dae161e27b0e    4.7 GB    11 days ago      
llama3.1:8b                                              46e0c10c039e    4.9 GB    11 days ago      
llama3:latest                                            365c0bd3c000    4.7 GB    6 weeks ago      
```

## Result

GO.

- `/mnt/spirit-8tb` is mounted as ext4 with available capacity.
- `hermes4:latest` is visible in `ollama list`.
- Ollama model storage is proven through `/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models`.
- Direct process environment inspection was blocked by `/proc/$pid/environ` permissions, so `OLLAMA_MODELS` was not directly proven from the running process. The active symlink path proves the default Ollama model home resolves onto the 8TB drive.
