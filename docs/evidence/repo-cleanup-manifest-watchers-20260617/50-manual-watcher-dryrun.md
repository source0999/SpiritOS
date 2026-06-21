# Manual Watcher Dry Run

Raw outputs are saved under `raw/watcher-dryrun/`. No services were restarted and no watcher was installed.

- `00-date.txt`: exit 0; 2026-06-17T22:13:55-04:00
- `01-uptime.txt`: exit 0; 22:13:55 up  1:06,  9 users,  load average: 2.03, 3.63, 3.71
- `02-free.txt`: exit 0; total        used        free      shared  buff/cache   available; Mem:            15Gi       7.6Gi       1.1Gi       145Mi       7.3Gi       7.9Gi; Swap:          4.0Gi       973Mi       3.0Gi
- `03-df.txt`: exit 0; Filesystem      Size  Used Avail Use% Mounted on; /dev/sdb2       457G  282G  152G  65% /; /dev/sda1       7.3T  156G  6.8T   3% /mnt/spirit-8tb
- `04-ports.txt`: exit 0; LISTEN 0      2048                       0.0.0.0:8787       0.0.0.0:*    users:(("python",pid=35581,fd=14)); LISTEN 0      511                        0.0.0.0:3000       0.0.0.0:*    users:(("next-server (v1",pid=36213,fd=19)); LISTEN 0      2048                     127.0.0.1:8797       0.0.0.0:*
- `05-systemctl-failed.txt`: exit 0; UNIT                         LOAD   ACTIVE SUB    DESCRIPTION; ● mnt-spirit\x2dprojects.mount loaded failed failed /mnt/spirit-projects
- `06-systemctl-ollama-docker.txt`: exit 0; ● ollama.service - Ollama Service; Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: enabled); Active: active (running) since Wed 2026-06-17 21:08:13 EDT; 1h 5min ago
- `07-docker-ps.txt`: exit 0; NAMES                    STATUS                         PORTS; spirit-jellyfin          Up About an hour (healthy)     0.0.0.0:8096->8096/tcp, [::]:8096->8096/tcp; scout_v0_1               Up About an hour (healthy)     0.0.0.0:8077->8077/tcp, [::]:8077->8077/tcp
- `08-tmux-ls.txt`: exit 0; face-organizer-8765: 1 windows (created Wed Jun 17 22:01:46 2026); source-proxy-lan: 1 windows (created Wed Jun 17 21:57:57 2026); spiritos-lan: 1 windows (created Wed Jun 17 21:58:12 2026)
- `09-source-proxy-health.txt`: exit 0; {"detail":"Not Found"}
- `10-source-proxy-v1-health.txt`: exit 0; {"detail":"Not Found"}
- `11-next-root.txt`: exit 0; no output
- `12-ollama-tags.txt`: exit 0; {"models":[{"name":"gemma3n:e4b","model":"gemma3n:e4b","modified_at":"2026-06-09T22:36:50.88396207-04:00","size":7547589116,"digest":"15cb39fd9394fd2549f6df9081cfc84dd134ecf2c9c5be911e5629920489ac32","details":{"parent_model":"","format":"gguf","family":"gemma3n","families":["gemma3n"],"parameter_si
- `13-journal-warning-tail.txt`: exit 0; Jun 17 21:07:20 source-server kernel: x86/cpu: SGX disabled by BIOS.; Jun 17 21:07:20 source-server kernel: Transient Scheduler Attacks: MDS CPU bug present and SMT on, data leak possible. See https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/mds.html for more details.; Jun 17 21:07:20 sour
- `14-kernel-tail.txt`: exit 0; Jun 17 21:07:32 source-server kernel: lp: driver loaded but no devices found; Jun 17 21:07:32 source-server kernel: ppdev: user-space parallel port driver; Jun 17 21:07:32 source-server systemd-journald[398]: File /var/log/journal/fdf9c5317dea491980c6866513254417/system.journal corrupted or uncleanl
