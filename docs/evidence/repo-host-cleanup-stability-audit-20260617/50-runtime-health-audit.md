# Runtime Health Audit

## Port Listeners

```
LISTEN 0      2048                     127.0.0.1:8797       0.0.0.0:*    users:(("headroom",pid=9253,fd=8))
LISTEN 0      4096                       0.0.0.0:8096       0.0.0.0:*
LISTEN 0      4096                     127.0.0.1:11434      0.0.0.0:*
LISTEN 0      4096                          [::]:8096          [::]:*
```

## tmux Sessions

```
error connecting to /tmp/tmux-1000/default (No such file or directory)
```

## Process Pressure

Top memory:

```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root        3062  1.8 11.7 7248196 1918192 ?     SLsl 21:09   0:46 /usr/local/bin/python /usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 80
source     14017 12.9  2.3 12077772 374880 ?     Sl   21:25   3:32 /home/source/.zcode/server/node /home/source/.zcode/server/zcode-server.cjs
source      9253  6.9  1.3 930436 223968 pts/2   Sl+  21:16   2:32 /home/source/SpiritOS/.venv-headroom/bin/python3 /home/source/SpiritOS/.venv-headroom/bin/headroom proxy --host 127.0.0.1 --port 8797
root        3049  0.6  1.3 273525320 215232 ?    Ssl  21:09   0:17 /jellyfin/jellyfin
source     25052  1.9  1.2 43975812 203772 ?     Sl   21:48   0:05 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node --dns-result-order=ipv4first --inspect-port=0 --experimental-network-inspection /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=extensionHost --transformURIs --useHostProxy=false
source     14108  0.2  1.1 1282056 180760 ?      Ssl  21:25   0:04 zcode-cli
root        3073  0.5  0.9 556724 157872 ?       Ssl  21:09   0:13 /usr/local/bin/python3.12 /usr/local/bin/uvicorn scout.main:app --host 0.0.0.0 --port 8077
source      3436  0.7  0.8 807552 143604 ?       Ssl  21:09   0:20 /home/ubuntu/faster-whisper-server/.venv/bin/python /home/ubuntu/faster-whisper-server/.venv/bin/uvicorn --factory faster_whisper_server.main:create_app
source     25059  0.9  0.7 11795128 128016 ?     Sl   21:48   0:02 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=fileWatcher
source      4824  1.4  0.6 11814816 104320 ?     Sl   21:10   0:37 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/server-main.js --start-server --host 127.0.0.1 --port 0 --connection-token-file /run/user/1000/cursor-remote-code.token.19454fe0852788c8224fe18079719738 --telemetry-level off --enable-remote-auto-shutdown --accept-server-license-terms
root        1749  0.0  0.5 26002696 91468 tty7   Ssl+ 21:08   0:01 /usr/lib/xorg/Xorg -core :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch
root        5863  0.0  0.5 659244 90468 ?        Sl   21:10   0:02 searxng worker-1
lightdm     2106  0.0  0.5 895220 84304 ?        Sl   21:09   0:00 /usr/sbin/unity-greeter
root        6499  0.2  0.5 1293972 84272 ?       Ssl  21:11   0:05 /usr/bin/casaos-app-management -c /etc/casaos/app-management.conf
source      5667  0.2  0.4 11681152 67956 ?      Sl   21:10   0:06 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=ptyHost --logsPath /home/source/.cursor-server/data/logs/20260617T211018
source      1888  7.3  0.3 175276 63664 ?        Sl   21:08   3:12 smbd: client [10.0.0.126]
source      9241  0.0  0.3 1093012 54288 pts/2   Sl+  21:16   0:00 npm run headroom:proxy
root        1436  0.4  0.3 1355704 49252 ?       Ssl  21:08   0:13 /usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock --port=41641
root        2004  0.4  0.2 3502380 48556 ?       Ssl  21:09   0:11 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
source      4189  0.0  0.2 990060 47040 ?        Sl   21:10   0:00 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/multiplex-server/123cc5ffb7498a31f4e8e7bd38493b242868aa65b5035edad965fd5c419c5c96.js b75301ab-8c9d-41c4-b4ff-91034184d839 0
root        6641  0.2  0.2  59168 42496 ?        S    21:11   0:05 python speech.py --xtts_device none
root        1644  0.1  0.2 774160 37040 ?        Ssl  21:08   0:03 /usr/bin/casaos-local-storage -c /etc/casaos/local-storage.conf
root        6675  0.0  0.1 479988 31876 ?        Ssl  21:11   0:00 /usr/libexec/fwupd/fwupd
root        1446  0.3  0.1 1261888 29280 ?       Ssl  21:08   0:08 /usr/bin/cloudflared --no-autoupdate tunnel run --token eyJhIjoiNjUzMzc2MzBmNWZlODNlZTUyODFmOGQ2NDdmMDhhZjUiLCJ0IjoiNzc1MWY3NjEtZGIwYy00NzZlLWJmNWItOGFkZWExNjdiNGZhIiwicyI6Ik1UWXlOVFZtWlRRdFpEQmtNUzAwWkdNd0xUaGxZMll0TUdSbU5HVTBNemxsT1RjeiJ9
root         444  0.0  0.1 289116 27452 ?        SLsl 21:07   0:00 /sbin/multipathd -d -s
lightdm     2077  0.0  0.1 565040 27452 ?        S<sl 21:09   0:00 /usr/bin/wireplumber
root        1440  0.3  0.1 2320036 26972 ?       Ssl  21:08   0:08 /usr/bin/containerd
root        1002  0.0  0.1 763020 23828 ?        Ssl  21:07   0:00 /usr/bin/rclone rcd --rc-addr unix:///var/run/rclone/rclone.sock --rc-no-auth --rc-allow-origin *
root        1503  0.0  0.1 1255780 21512 ?       Ssl  21:08   0:01 /usr/bin/casaos-message-bus -c /etc/casaos/message-bus.conf
lightdm     2183  0.0  0.1 531588 21112 ?        Sl   21:09   0:00 /usr/lib/unity-settings-daemon/unity-settings-daemon
ollama      1448  0.0  0.1 2160960 21088 ?       Ssl  21:08   0:00 /usr/local/bin/ollama serve
root        1706  0.0  0.1  90388 20848 ?        Ss   21:08   0:00 /usr/sbin/smbd --foreground --no-process-group
source     22764  0.0  0.1  27692 20072 ?        Ss   21:44   0:00 python3 -
root        1437  0.0  0.1 109688 17452 ?        Ssl  21:08   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
lightdm     2187  0.0  0.1 444700 17332 ?        Ssl  21:09   0:00 /usr/libexec/indicator-keyboard/indicator-keyboard-service --use-gtk
root        1518  0.1  0.1 1253784 17272 ?       Ssl  21:08   0:04 /usr/bin/casaos -c /etc/casaos/casaos.conf
root         398  0.0  0.1  59008 16820 ?        S<s  21:07   0:01 /usr/lib/systemd/systemd-journald
lightdm     2176  0.0  0.1 494744 16516 ?        Sl   21:09   0:00 nm-applet
cups-br+    1578  0.0  0.1 268500 16512 ?        Ssl  21:08   0:00 /usr/sbin/cups-browsed
```

Top CPU:

```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
source     14017 12.9  2.3 12077772 374880 ?     Sl   21:25   3:32 /home/source/.zcode/server/node /home/source/.zcode/server/zcode-server.cjs
source      1888  7.3  0.3 175276 63664 ?        Sl   21:08   3:12 smbd: client [10.0.0.126]
source      9253  6.9  1.3 930436 223968 pts/2   Sl+  21:16   2:32 /home/source/SpiritOS/.venv-headroom/bin/python3 /home/source/SpiritOS/.venv-headroom/bin/headroom proxy --host 127.0.0.1 --port 8797
source     25052  1.9  1.2 43975812 203772 ?     Sl   21:48   0:05 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node --dns-result-order=ipv4first --inspect-port=0 --experimental-network-inspection /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=extensionHost --transformURIs --useHostProxy=false
root        3062  1.8 11.7 7248196 1918192 ?     SLsl 21:09   0:46 /usr/local/bin/python /usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 80
source      4824  1.4  0.6 11814816 104320 ?     Sl   21:10   0:37 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/server-main.js --start-server --host 127.0.0.1 --port 0 --connection-token-file /run/user/1000/cursor-remote-code.token.19454fe0852788c8224fe18079719738 --telemetry-level off --enable-remote-auto-shutdown --accept-server-license-terms
source     25059  0.9  0.7 11795128 128024 ?     Sl   21:48   0:02 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=fileWatcher
source      3436  0.7  0.8 807552 143604 ?       Ssl  21:09   0:20 /home/ubuntu/faster-whisper-server/.venv/bin/python /home/ubuntu/faster-whisper-server/.venv/bin/uvicorn --factory faster_whisper_server.main:create_app
root        3049  0.6  1.3 273525320 215232 ?    Ssl  21:09   0:17 /jellyfin/jellyfin
root        3073  0.5  0.9 556724 157872 ?       Ssl  21:09   0:13 /usr/local/bin/python3.12 /usr/local/bin/uvicorn scout.main:app --host 0.0.0.0 --port 8077
root        1436  0.4  0.3 1355704 49252 ?       Ssl  21:08   0:13 /usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock --port=41641
root        2004  0.4  0.2 3502380 48556 ?       Ssl  21:09   0:11 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root        1446  0.3  0.1 1261888 29280 ?       Ssl  21:08   0:08 /usr/bin/cloudflared --no-autoupdate tunnel run --token eyJhIjoiNjUzMzc2MzBmNWZlODNlZTUyODFmOGQ2NDdmMDhhZjUiLCJ0IjoiNzc1MWY3NjEtZGIwYy00NzZlLWJmNWItOGFkZWExNjdiNGZhIiwicyI6Ik1UWXlOVFZtWlRRdFpEQmtNUzAwWkdNd0xUaGxZMll0TUdSbU5HVTBNemxsT1RjeiJ9
root        1440  0.3  0.1 2320036 26972 ?       Ssl  21:08   0:08 /usr/bin/containerd
avahi        934  0.2  0.0   8900  4284 ?        Ss   21:07   0:07 avahi-daemon: running [source-server.local]
source      5667  0.2  0.4 11681152 67956 ?      Sl   21:10   0:06 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/out/bootstrap-fork --type=ptyHost --logsPath /home/source/.cursor-server/data/logs/20260617T211018
source     14108  0.2  1.1 1282056 180760 ?      Ssl  21:25   0:04 zcode-cli
root        6499  0.2  0.5 1293972 84272 ?       Ssl  21:11   0:05 /usr/bin/casaos-app-management -c /etc/casaos/app-management.conf
root        6641  0.2  0.2  59168 42496 ?        S    21:11   0:05 python speech.py --xtts_device none
root        1518  0.1  0.1 1253784 17272 ?       Ssl  21:08   0:04 /usr/bin/casaos -c /etc/casaos/casaos.conf
source     24884  0.1  0.0  15968  8104 ?        S    21:48   0:00 sshd: source@notty
root         168  0.1  0.0      0     0 ?        I<   21:06   0:03 [kworker/7:1H-kblockd]
root          17  0.1  0.0      0     0 ?        I    21:06   0:03 [rcu_preempt]
root        1790  0.1  0.0  87816  5828 ?        S    21:08   0:03 smbd: notifyd .
root        1644  0.1  0.2 774160 37044 ?        Ssl  21:08   0:03 /usr/bin/casaos-local-storage -c /etc/casaos/local-storage.conf
source     29391  0.1  0.0  11516  8464 pts/0    Ss+  21:52   0:00 -bash
root           1  0.0  0.0  23032 12560 ?        Ss   21:06   0:02 /sbin/init
root          90  0.0  0.0      0     0 ?        S    21:06   0:02 [kswapd0]
root        5863  0.0  0.5 659244 90468 ?        Sl   21:10   0:02 searxng worker-1
root         330  0.0  0.0      0     0 ?        D    21:07   0:02 [jbd2/sdb2-8]
root         398  0.0  0.1  59008 16820 ?        S<s  21:07   0:01 /usr/lib/systemd/systemd-journald
root        2897  0.0  0.0 1235412 8208 ?        Sl   21:09   0:01 /usr/bin/containerd-shim-runc-v2 -namespace moby -id 20ba507f2f53ede7721a4476162d9ce39fa346a287e21ea6584715067603d8e5 -address /run/containerd/containerd.sock
root        1503  0.0  0.1 1255780 21512 ?       Ssl  21:08   0:01 /usr/bin/casaos-message-bus -c /etc/casaos/message-bus.conf
root       29346  0.0  0.0  14780 10544 ?        Ss   21:52   0:00 sshd: source [priv]
root       17904  0.0  0.0      0     0 ?        I    21:33   0:00 [kworker/1:2-i915-unordered]
root        1749  0.0  0.5 26002696 91468 tty7   Ssl+ 21:08   0:01 /usr/lib/xorg/Xorg -core :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch
source     24885  0.0  0.0   8648  5040 ?        Ss   21:48   0:00 bash
root         153  0.0  0.0      0     0 ?        I<   21:06   0:01 [kworker/0:1H-kblockd]
root       20807  0.0  0.0      0     0 ?        I    21:40   0:00 [kworker/1:3-cgroup_free]
```

## Failed/System Services

```
  UNIT                         LOAD   ACTIVE SUB    DESCRIPTION
● mnt-spirit\x2dprojects.mount loaded failed failed /mnt/spirit-projects

Legend: LOAD   → Reflects whether the unit definition was properly loaded.
        ACTIVE → The high-level unit activation state, i.e. generalization of SUB.
        SUB    → The low-level unit activation state, values depend on unit type.

1 loaded units listed.
```

```
● ollama.service - Ollama Service
     Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-06-17 21:08:13 EDT; 44min ago
   Main PID: 1448 (ollama)
      Tasks: 13 (limit: 18962)
     Memory: 103.9M (peak: 441.6M)
        CPU: 1.946s
     CGroup: /system.slice/ollama.service
             └─1448 /usr/local/bin/ollama serve

Jun 17 21:08:29 source-server ollama[1448]: time=2026-06-17T21:08:29.861-04:00 level=INFO source=runner.go:67 msg="discovering available GPUs..."
Jun 17 21:08:29 source-server ollama[1448]: time=2026-06-17T21:08:29.904-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 38321"
Jun 17 21:08:50 source-server ollama[1448]: time=2026-06-17T21:08:47.032-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 36023"
Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=runner.go:106 msg="experimental Vulkan support disabled.  To enable, set OLLAMA_VULKAN=1"
Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 35011"
Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 43967"
Jun 17 21:09:05 source-server ollama[1448]: time=2026-06-17T21:09:05.158-04:00 level=INFO source=types.go:42 msg="inference compute" id=GPU-bd0daa29-1aa2-b006-4f01-a3b10d85b36a filter_id="" library=CUDA compute=8.6 name=CUDA0 description="NVIDIA GeForce RTX 3060" libdirs=ollama,cuda_v13 driver=13.0 pci_id=0000:01:00.0 type=discrete total="12.0 GiB" available="11.6 GiB"
Jun 17 21:09:05 source-server ollama[1448]: time=2026-06-17T21:09:05.158-04:00 level=INFO source=routes.go:1860 msg="vram-based default context" total_vram="12.0 GiB" default_num_ctx=4096
Jun 17 21:47:31 source-server ollama[1448]: [GIN] 2026/06/17 - 21:47:31 | 200 |   112.54033ms |       127.0.0.1 | HEAD     "/"
Jun 17 21:47:31 source-server ollama[1448]: [GIN] 2026/06/17 - 21:47:31 | 200 |  184.986867ms |       127.0.0.1 | GET      "/api/tags"

● docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/docker.service.d
             └─override.conf
     Active: active (running) since Wed 2026-06-17 21:11:29 EDT; 41min ago
TriggeredBy: ● docker.socket
       Docs: https://docs.docker.com
   Main PID: 2004 (dockerd)
      Tasks: 138
     Memory: 88.1M (peak: 181.3M swap: 17.7M swap peak: 18.6M)
        CPU: 12.552s
     CGroup: /system.slice/docker.service
             ├─2004 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
             ├─3152 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8080 -container-ip 172.18.0.2 -container-port 8080 -use-listen-fd
             ├─3159 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8080 -container-ip 172.18.0.2 -container-port 8080 -use-listen-fd
             ├─3195 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5200 -container-ip 172.18.0.3 -container-port 8000 -use-listen-fd
             ├─3204 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 5200 -container-ip 172.18.0.3 -container-port 8000 -use-listen-fd
             ├─3241 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5432 -container-ip 172.18.0.4 -container-port 5432 -use-listen-fd
             ├─3248 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 5432 -container-ip 172.18.0.4 -container-port 5432 -use-listen-fd
             ├─3270 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8096 -container-ip 172.20.0.2 -container-port 8096 -use-listen-fd
             ├─3277 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8096 -container-ip 172.20.0.2 -container-port 8096 -use-listen-fd
             ├─3301 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8077 -container-ip 172.18.0.5 -container-port 8077 -use-listen-fd
             ├─3310 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8077 -container-ip 172.18.0.5 -container-port 8077 -use-listen-fd
             ├─3350 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8020 -container-ip 172.18.0.6 -container-port 80 -use-listen-fd
             ├─3358 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8020 -container-ip 172.18.0.6 -container-port 80 -use-listen-fd
             ├─6213 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8000 -container-ip 172.18.0.7 -container-port 8000 -use-listen-fd
             └─6220 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8000 -container-ip 172.18.0.7 -container-port 8000 -use-listen-fd

Jun 17 21:50:52 source-server dockerd[2004]: time="2026-06-17T21:50:52.818410187-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.902833853-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.902857326-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.904345409-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:51:52 source-server dockerd[2004]: time="2026-06-17T21:51:52.959599632-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:51:52 source-server dockerd[2004]: time="2026-06-17T21:51:52.959600869-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:51:52 source-server dockerd[2004]: time="2026-06-17T21:51:52.960961077-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:52:23 source-server dockerd[2004]: time="2026-06-17T21:52:23.008946779-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:52:23 source-server dockerd[2004]: time="2026-06-17T21:52:23.008947889-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:52:23 source-server dockerd[2004]: time="2026-06-17T21:52:23.010312891-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
```

## Docker

```
NAMES                    STATUS                      PORTS
spirit-jellyfin          Up 43 minutes (healthy)     0.0.0.0:8096->8096/tcp, [::]:8096->8096/tcp
scout_v0_1               Up 43 minutes (healthy)     0.0.0.0:8077->8077/tcp, [::]:8077->8077/tcp
spirit-searxng           Up 43 minutes (healthy)     0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
source-postgres          Up 43 minutes (healthy)     0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
spirit-openedai-speech   Up 43 minutes (healthy)     0.0.0.0:5200->8000/tcp, [::]:5200->8000/tcp
spirit-whisper           Up 43 minutes (unhealthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
spirit-xtts              Up 43 minutes (healthy)     0.0.0.0:8020->80/tcp, [::]:8020->80/tcp
```

```

```

## Endpoint Checks

Source Proxy `/health`:

```

```

Source Proxy `/v1/health`:

```

```

Next/dev server `:3000` response head:

```

```

Ollama tags response head:

```
{"models":[{"name":"gemma3n:e4b","model":"gemma3n:e4b","modified_at":"2026-06-09T22:36:50.88396207-04:00","size":7547589116,"digest":"15cb39fd9394fd2549f6df9081cfc84dd134ecf2c9c5be911e5629920489ac32","details":{"parent_model":"","format":"gguf","family":"gemma3n","families":["gemma3n"],"parameter_size":"6.9B","quantization_level":"Q4_K_M"}},{"name":"hermes4:latest","model":"hermes4:latest","modified_at":"2026-05-29T19:47:02.020002088-04:00","size":9001755837,"digest":"3e79497c964380ab2cf68708d4b1dce602484aa3989bc5d2322630efc6e731a7","details":{"parent_model":"","format":"gguf","family":"qwen3","families":["qwen3"],"parameter_size":"14.8B","quantization_level":"Q4_K_M"}},{"name":"hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M","model":"hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M","modified_at":"2026-05-29T19:45:49.353447581-04:00","size":9001755690,"digest":"ce5cb56a789801c7b6c575b313d5f3779a4d208c742c2f8f3fd43393e90d92a5","details":{"parent_model":"","format":"gguf","family":"qwen3","families":["qwen3"],"parameter_size":"14.8B","quantization_level":"unknown"}},{"name":"hermes3:8b-abliterated","model":"hermes3:8b-abliterated","modified_at":"2026-05-24T22:02:47.182678608-04:00","size":4675905733,"digest":"621eb9c2e65e986b4ab002c354e4da35d7041a746dcec0bbcb67b5f2c70e1f3f","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"8.0B","quantization_level":"Q4_0"}},{"name":"mannix/llama3-8b-ablitered-v3:latest","model":"mannix/llama3-8b-ablitered-v3:latest","modified_at":"2026-05-24T22:02:36.820607791-04:00","size":4675905733,"digest":"46688a22037ee2799d368c0c0497c38f53d596a10fd3a201089f7e6ea8477301","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"8.0B","quantization_level":"Q4_0"}},{"name":"qwen2.5-coder:7b","model":"qwen2.5-coder:7b","modified_at":"2026-05-17T21:36:01.722215506-04:00","size":4683087561,"digest":"dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364","details":{"parent_model":"","format":"gguf","family":"qwen2","families":["qwen2"],"parameter_size":"7.6B","quantization_level":"Q4_K_M"}},{"name":"llama3.1:8b","model":"llama3.1:8b","modified_at":"2026-05-17T21:25:37.251728579-04:00","size":4920753328,"digest":"46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"8.0B","quantization_level":"Q4_K_M"}},{"name":"llama3:latest","model":"llama3:latest","modified_at":"2026-04-16T23:00:59.305368764-04:00","size":4661224676,"digest":"365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"8.0B","quantization_level":"Q4_0"}}]}
```

## Classification

- Source Proxy on 8787: not proven healthy by curl; inspect listener and tmux/systemd evidence above.
- Next/dev server on 3000: not responding to HTTP in this audit.
- Ollama: see systemd status and `:11434` response above.
- Docker/SearXNG/Jellyfin: see Docker and listener evidence.
- Fragility: anything running only in tmux/npm/dev shell without systemd supervision is healthy-but-fragile for unattended recovery.


## Auditor Synthesis

- Source Proxy `:8787`: NO-GO at audit time. `ss` showed no listener on `:8787`, and both `https://127.0.0.1:8787/health` and `/v1/health` returned empty output.
- Next/dev server `:3000`: NO-GO at audit time. `ss` showed no listener on `:3000`, and `curl http://127.0.0.1:3000` returned empty output.
- tmux supervision: no tmux server was reachable (`error connecting to /tmp/tmux-1000/default`), so proxy/dev-server tmux supervision was not present at audit time.
- Ollama: active under systemd, listening on `127.0.0.1:11434`, and `/api/tags` responded.
- Docker/Jellyfin/SearXNG: Docker is active; Jellyfin, SearXNG, Postgres, openedai-speech, scout, and XTTS containers were up, while `spirit-whisper` was `unhealthy`.
- Failed unit: `/mnt/spirit-projects` mount is failed; this is separate from `/mnt/spirit-8tb` but should be watched because failed mounts can create confusing runtime assumptions.
