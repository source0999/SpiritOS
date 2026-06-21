# Dell Stability Audit

## Confirmed Evidence

- Current time: `2026-06-17T21:47:32-04:00`
- Boot start: `2026-06-17 21:06:58`
- Raw boot/session history: `raw/40_last_x_120.txt`, `raw/40_journal_boots.txt`.

## Last / Boot History

```
runlevel (to lvl 5)   6.8.0-124-generi Wed Jun 17 21:11   still running
source   pts/0        100.82.31.124    Wed Jun 17 21:09   still logged in
reboot   system boot  6.8.0-124-generi Wed Jun 17 21:07   still running
source   pts/7        tmux(14286).%26  Wed Jun 17 06:03 - crash  (15:04)
source   pts/7        tmux(14286).%25  Wed Jun 17 05:51 - 06:03  (00:11)
source   pts/6        tmux(14286).%24  Wed Jun 17 05:45 - crash  (15:21)
source   pts/8        100.82.31.124    Wed Jun 17 05:41 - 20:59  (15:18)
source   pts/7        tmux(14286).%23  Tue Jun 16 20:51 - 05:51  (09:00)
source   pts/7        tmux(14286).%22  Tue Jun 16 20:14 - 20:51  (00:36)
source   pts/6        tmux(14286).%21  Tue Jun 16 20:08 - 05:45  (09:37)
source   pts/3        tmux(14286).%20  Tue Jun 16 19:49 - crash (1+01:17)
source   pts/5        tmux(14286).%19  Tue Jun 16 19:49 - crash (1+01:17)
source   pts/6        tmux(14286).%18  Tue Jun 16 19:48 - 20:08  (00:19)
source   pts/6        tmux(14286).%17  Tue Jun 16 19:17 - 19:48  (00:31)
source   pts/6        tmux(14286).%16  Tue Jun 16 19:10 - 19:17  (00:06)
source   pts/6        tmux(14286).%15  Tue Jun 16 19:06 - 19:10  (00:03)
source   pts/5        tmux(14286).%14  Tue Jun 16 19:06 - 19:49  (00:42)
source   pts/6        tmux(14286).%13  Tue Jun 16 19:01 - 19:05  (00:03)
source   pts/5        tmux(14286).%12  Tue Jun 16 19:01 - 19:06  (00:05)
source   pts/2        tmux(14286).%11  Tue Jun 16 16:13 - crash (1+04:54)
source   pts/6        tmux(14286).%10  Tue Jun 16 16:00 - 16:41  (00:40)
source   pts/2        tmux(14286).%9   Tue Jun 16 15:55 - 16:00  (00:05)
source   pts/2        tmux(14286).%8   Tue Jun 16 15:46 - 15:52  (00:05)
source   pts/2        tmux(14286).%7   Tue Jun 16 15:40 - 15:46  (00:05)
source   pts/2        tmux(14286).%6   Tue Jun 16 15:34 - 15:39  (00:05)
source   pts/5        tmux(14286).%5   Tue Jun 16 15:31 - 16:13  (00:41)
source   pts/2        tmux(14286).%4   Tue Jun 16 15:25 - 15:34  (00:09)
source   pts/2        tmux(14286).%3   Tue Jun 16 15:08 - 15:25  (00:16)
source   pts/4        tmux(14286).%2   Tue Jun 16 14:57 - 16:13  (01:15)
source   pts/3        tmux(14286).%1   Tue Jun 16 14:54 - 19:49  (04:54)
source   pts/2        tmux(14286).%0   Tue Jun 16 14:53 - 15:08  (00:14)
runlevel (to lvl 5)   6.8.0-124-generi Tue Jun 16 14:45 - 21:11 (1+06:26)
source   pts/0        100.82.31.124    Tue Jun 16 14:45 - 14:45  (00:00)
reboot   system boot  6.8.0-124-generi Tue Jun 16 14:41   still running
source   pts/3        tmux(15354).%226 Tue Jun 16 00:36 - 00:42  (00:05)
source   pts/1        tmux(15354).%225 Mon Jun 15 22:26 - crash  (16:15)
source   pts/7        tmux(15354).%224 Mon Jun 15 18:03 - crash  (20:37)
source   pts/6        tmux(15354).%223 Mon Jun 15 01:32 - crash (1+13:08)
source   pts/5        tmux(15354).%222 Mon Jun 15 01:03 - 00:33  (23:30)
source   pts/5        tmux(15354).%221 Mon Jun 15 00:28 - 01:02  (00:34)
source   pts/7        tmux(15354).%220 Sun Jun 14 23:20 - 23:21  (00:01)
source   pts/6        tmux(15354).%219 Sun Jun 14 23:20 - 00:14  (00:53)
source   pts/6        tmux(15354).%218 Sun Jun 14 23:16 - 23:16  (00:00)
source   pts/5        tmux(15354).%217 Sun Jun 14 23:06 - 00:15  (01:08)
source   pts/5        tmux(15354).%216 Sun Jun 14 23:04 - 23:04  (00:00)
source   pts/3        tmux(15354).%215 Sun Jun 14 22:48 - 22:25  (23:37)
source   pts/5        tmux(15354).%214 Sun Jun 14 20:56 - 22:48  (01:51)
source   pts/5        tmux(15354).%213 Sun Jun 14 16:32 - 18:01  (01:29)
source   pts/3        tmux(15354).%212 Sun Jun 14 16:32 - 20:56  (04:24)
source   pts/9        tmux(15354).%211 Sun Jun 14 12:36 - 13:41  (01:04)
source   pts/9        tmux(15354).%210 Sun Jun 14 12:36 - 12:36  (00:00)
source   pts/5        tmux(15354).%209 Sun Jun 14 12:35 - 16:32  (03:56)
source   pts/9        tmux(15354).%208 Sun Jun 14 11:43 - 12:19  (00:36)
source   pts/9        tmux(15354).%207 Sun Jun 14 11:31 - 11:36  (00:05)
source   pts/9        tmux(15354).%206 Sun Jun 14 11:30 - 11:31  (00:00)
source   pts/5        tmux(15354).%205 Sun Jun 14 11:30 - 12:35  (01:05)
source   pts/9        tmux(15354).%204 Sun Jun 14 10:35 - 11:12  (00:37)
source   pts/5        tmux(15354).%203 Sun Jun 14 10:34 - 11:29  (00:55)
source   pts/9        tmux(15354).%202 Sun Jun 14 10:06 - 10:34  (00:27)
source   pts/5        tmux(15354).%201 Sun Jun 14 09:27 - 10:34  (01:06)
source   pts/5        tmux(15354).%200 Sun Jun 14 09:27 - 09:27  (00:00)
source   pts/5        tmux(15354).%199 Sun Jun 14 09:27 - 09:27  (00:00)
source   pts/9        tmux(15354).%198 Sun Jun 14 08:17 - 09:26  (01:08)
source   pts/5        tmux(15354).%197 Sun Jun 14 08:10 - 08:17  (00:06)
source   pts/5        tmux(15354).%196 Sun Jun 14 08:00 - 08:10  (00:09)
source   pts/9        tmux(15354).%195 Sun Jun 14 07:49 - 08:00  (00:10)
source   pts/9        tmux(15354).%194 Sun Jun 14 07:35 - 07:49  (00:13)
source   pts/5        tmux(15354).%193 Sun Jun 14 07:33 - 07:54  (00:20)
source   pts/9        tmux(15354).%192 Sun Jun 14 07:28 - 07:35  (00:07)
source   pts/5        tmux(15354).%191 Sun Jun 14 07:24 - 07:33  (00:09)
source   pts/9        tmux(15354).%190 Sun Jun 14 07:16 - 07:28  (00:11)
source   pts/5        tmux(15354).%189 Sun Jun 14 07:14 - 07:16  (00:02)
source   pts/10       tmux(15354).%188 Sun Jun 14 07:12 - 07:24  (00:12)
source   pts/9        tmux(15354).%187 Sun Jun 14 07:03 - 07:12  (00:08)
source   pts/5        tmux(15354).%186 Sun Jun 14 06:59 - 07:14  (00:14)
source   pts/10       tmux(15354).%185 Sun Jun 14 06:53 - 06:59  (00:05)
source   pts/5        tmux(15354).%184 Sun Jun 14 06:53 - 06:53  (00:00)
source   pts/2        tmux(15354).%183 Sat Jun 13 23:42 - crash (2+14:58)
source   pts/9        tmux(15354).%182 Sat Jun 13 23:39 - 07:03  (07:24)
source   pts/5        tmux(15354).%181 Sat Jun 13 23:36 - 23:39  (00:02)
source   pts/10       tmux(15354).%180 Sat Jun 13 23:36 - 06:53  (07:17)
source   pts/5        tmux(15354).%179 Sat Jun 13 23:35 - 23:36  (00:00)
source   pts/10       tmux(15354).%178 Sat Jun 13 23:28 - 23:35  (00:07)
source   pts/9        tmux(15354).%177 Sat Jun 13 23:24 - 23:36  (00:11)
source   pts/5        tmux(15354).%176 Sat Jun 13 23:21 - 23:28  (00:06)
source   pts/2        tmux(15354).%175 Sat Jun 13 23:06 - 23:42  (00:36)
source   pts/10       tmux(15354).%174 Sat Jun 13 22:28 - 23:21  (00:53)
source   pts/9        tmux(15354).%173 Sat Jun 13 22:25 - 23:24  (00:59)
source   pts/0        100.82.31.124    Sat Jun 13 22:15 - 04:08 (2+05:53)
source   pts/5        tmux(15354).%172 Sat Jun 13 22:10 - 22:28  (00:18)
source   pts/1        100.82.31.124    Sat Jun 13 22:07 - 18:31 (1+20:23)
source   pts/0        tmux(15354).%171 Sat Jun 13 22:07 - 22:10  (00:03)
source   pts/5        tmux(15354).%170 Sat Jun 13 22:06 - 22:06  (00:00)
source   pts/7        tmux(15354).%169 Sat Jun 13 22:06 - 22:06  (00:00)
source   pts/5        tmux(15354).%168 Sat Jun 13 21:47 - 22:05  (00:18)
source   pts/7        tmux(15354).%167 Sat Jun 13 21:46 - 21:47  (00:00)
source   pts/5        tmux(15354).%166 Sat Jun 13 21:35 - 21:46  (00:10)
source   pts/7        tmux(15354).%165 Sat Jun 13 21:30 - 21:35  (00:05)
source   pts/5        tmux(15354).%164 Sat Jun 13 21:01 - 21:30  (00:28)
source   pts/8        tmux(15354).%163 Sat Jun 13 20:54 - 21:01  (00:06)
source   pts/5        tmux(15354).%162 Sat Jun 13 20:43 - 20:54  (00:10)
source   pts/8        tmux(15354).%161 Sat Jun 13 20:10 - 20:43  (00:33)
source   pts/5        tmux(15354).%160 Sat Jun 13 19:53 - 20:10  (00:17)
source   pts/5        tmux(15354).%159 Sat Jun 13 19:27 - 19:52  (00:25)
source   pts/2        tmux(15354).%158 Sat Jun 13 17:43 - 23:06  (05:22)
source   pts/3        10.0.0.186       Wed Jun 10 06:12 - 21:27 (3+15:15)
source   pts/10       tmux(15354).%157 Mon Jun  8 00:01 - 19:44  (19:43)
source   pts/10       tmux(15354).%156 Mon Jun  8 00:00 - 00:01  (00:00)
source   pts/10       tmux(15354).%155 Sun Jun  7 23:29 - 23:29  (00:00)
source   pts/10       tmux(15354).%154 Sun Jun  7 23:25 - 23:25  (00:00)
source   pts/9        tmux(15354).%153 Sun Jun  7 23:05 - 19:09 (5+20:03)
source   pts/2        tmux(15354).%152 Sun Jun  7 23:03 - 17:42 (5+18:38)
source   pts/8        10.0.0.186       Sun Jun  7 22:41 - 16:57  (18:16)
source   pts/2        tmux(15354).%151 Sun Jun  7 21:20 - 23:03  (01:42)
source   pts/2        tmux(15354).%150 Sun Jun  7 20:38 - 21:20  (00:42)
source   pts/2        tmux(15354).%149 Sun Jun  7 19:54 - 20:38  (00:43)
source   pts/2        tmux(15354).%148 Sun Jun  7 15:49 - 19:54  (04:05)
source   pts/2        tmux(15354).%147 Sun Jun  7 14:33 - 15:49  (01:15)
source   pts/2        tmux(15354).%146 Sun Jun  7 14:26 - 14:33  (00:07)
source   pts/2        tmux(15354).%145 Sun Jun  7 14:12 - 14:26  (00:13)
```

```
IDX BOOT ID                          FIRST ENTRY                 LAST ENTRY
-23 a984b1270adc48deb0817e84f21d6b1d Sat 2026-05-02 15:00:42 EDT Tue 2026-05-05 11:27:11 EDT
-22 9cf685a4547147c1a584767ba958a4c2 Tue 2026-05-05 11:30:23 EDT Sat 2026-05-09 10:30:12 EDT
-21 2e3e3b4d2c154d43bec1a0f8dcbe47ad Sat 2026-05-09 11:58:04 EDT Sun 2026-05-10 00:07:03 EDT
-20 df4d5a00e1d4488883a1b271968b8f6e Sun 2026-05-10 00:08:30 EDT Sun 2026-05-10 00:14:00 EDT
-19 d2fc83f54231489bbd3182ba5ef86f59 Sun 2026-05-10 00:14:53 EDT Sun 2026-05-17 20:32:20 EDT
-18 dba15c3fff454bab9c329e306ebdb2e3 Sun 2026-05-17 20:33:36 EDT Sun 2026-05-17 20:34:35 EDT
-17 9b779a0662744292b1272a115c73f8c7 Sun 2026-05-17 20:35:47 EDT Sun 2026-05-17 20:50:19 EDT
-16 12148c5bb95b4bf2adb84daebaa9a076 Sun 2026-05-17 20:50:57 EDT Sun 2026-05-17 20:52:17 EDT
-15 bb949b6136994094b448b69e8d9255f3 Sun 2026-05-17 20:53:23 EDT Sun 2026-05-17 22:14:13 EDT
-14 c72c53d9179d4b8982f6a92a6e5c5ff6 Sun 2026-05-17 22:19:32 EDT Sun 2026-05-17 22:41:10 EDT
-13 2fd0ed748ac6461a92fb9eb1a4da99a5 Sun 2026-05-17 23:15:40 EDT Sun 2026-05-17 23:35:55 EDT
-12 6214b396bcf84e4aaeb99c1a150d07ea Sun 2026-05-17 23:36:18 EDT Sun 2026-05-17 23:54:55 EDT
-11 f5c695cc056346c5bae406625604a9bf Sun 2026-05-17 23:55:46 EDT Sat 2026-05-23 09:58:38 EDT
-10 da7be2489a1c4e5fab68a69764a4d379 Sat 2026-05-23 10:00:59 EDT Sun 2026-05-24 21:11:03 EDT
 -9 1d3ffe1c13b54cdf85427b5aa3acaabd Sun 2026-05-24 21:14:57 EDT Mon 2026-05-25 18:43:12 EDT
 -8 60ba3b400c7544ef98caf35408f33da8 Mon 2026-05-25 18:49:02 EDT Mon 2026-05-25 23:32:47 EDT
 -7 782f778f5f294669945746ec1d30baf4 Mon 2026-05-25 23:34:19 EDT Mon 2026-05-25 23:37:05 EDT
 -6 fc73e8139e8c41bbb87ecf6fb76c0415 Mon 2026-05-25 23:38:57 EDT Thu 2026-05-28 20:28:33 EDT
 -5 070347dda707483b8c08d66636ca650a Thu 2026-05-28 20:39:15 EDT Thu 2026-05-28 20:42:15 EDT
 -4 a235b3fd6801461ab51d97a937f8cd8a Thu 2026-05-28 20:57:32 EDT Thu 2026-05-28 21:07:59 EDT
 -3 050b334ab6e34644a736dd413a98b9bf Thu 2026-05-28 21:08:36 EDT Tue 2026-06-02 20:37:13 EDT
 -2 e53d0b37bdfc4680b1770e25b0b95bd2 Tue 2026-06-02 20:38:27 EDT Tue 2026-06-16 14:40:14 EDT
 -1 6384ccff4db94bf59275d960f1f00a1e Tue 2026-06-16 14:41:19 EDT Wed 2026-06-17 21:00:11 EDT
  0 337fd0bcbf864f7f86cdf70d2b51aa23 Wed 2026-06-17 21:07:20 EDT Wed 2026-06-17 21:50:23 EDT
```

## Warning and Kernel Signals

Previous boot warnings:

```
Jun 16 14:42:17 source-server systemd[1]: Failed to mount mnt-spirit\x2dprojects.mount - /mnt/spirit-projects.
Jun 16 14:42:17 source-server systemd[1]: Dependency failed for remote-fs.target - Remote File Systems.
Jun 16 14:42:17 source-server (cron)[1639]: cron.service: Referenced but unset environment variable evaluates to an empty string: EXTRA_OPTS
Jun 16 14:42:18 source-server (smbd)[1699]: smbd.service: Referenced but unset environment variable evaluates to an empty string: SMBDOPTIONS
Jun 16 14:42:19 source-server lightdm[1648]: Seat type 'xlocal' is deprecated, use 'type=local' instead
Jun 16 14:42:41 source-server pipewire[1843]: mod.jackdbus-detect: Failed to receive jackdbus reply: org.freedesktop.DBus.Error.ServiceUnknown: The name org.jackaudio.service was not provided by any .service files
Jun 16 14:43:09 source-server pipewire[2152]: mod.jackdbus-detect: Failed to receive jackdbus reply: org.freedesktop.DBus.Error.ServiceUnknown: The name org.jackaudio.service was not provided by any .service files
Jun 16 14:43:10 source-server pipewire[2272]: mod.jackdbus-detect: Failed to receive jackdbus reply: org.freedesktop.DBus.Error.ServiceUnknown: The name org.jackaudio.service was not provided by any .service files
Jun 16 14:43:10 source-server lightdm[2248]: gkr-pam: couldn't unlock the login keyring.
Jun 16 14:43:21 source-server at-spi-bus-laun[2448]: Failed to register client: GDBus.Error:org.freedesktop.DBus.Error.UnknownMethod: No such method “RegisterClient”
Jun 16 14:43:22 source-server indicator-sound[2661]: volume-control-pulse.vala:741: unable to get pulse unix socket: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name org.PulseAudio1 was not provided by any .service files
Jun 16 14:43:22 source-server indicator-sound[2661]: media-player-list-greeter.vala:55: Unable to get active entry: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name com.canonical.UnityGreeter was not provided by any .service files
Jun 16 14:43:22 source-server indicator-keybo[2659]: gtk_icon_theme_get_for_screen: assertion 'GDK_IS_SCREEN (screen)' failed
Jun 16 14:43:24 source-server indicator-datet[2658]: could not find the desktop file for 'org.gnome.Calendar.desktop'
Jun 16 14:59:50 source-server xfce4-notifyd[18885]: cannot open display:
Jun 16 14:59:50 source-server systemd[2260]: xfce4-notifyd.service: Failed with result 'exit-code'.
Jun 16 14:59:50 source-server systemd[2260]: Failed to start xfce4-notifyd.service - XFCE notifications service.
Jun 16 15:26:06 source-server kernel: NVRM: nvCheckOkFailedNoLog: Check failed: Out of memory [NV_ERR_NO_MEMORY] (0x00000051) returned from _memdescAllocInternal(pMemDesc) @ mem_desc.c:1359
Jun 16 15:26:06 source-server kernel: NVRM: nvCheckOkFailedNoLog: Check failed: Out of memory [NV_ERR_NO_MEMORY] (0x00000051) returned from rmStatus @ system_mem.c:356
Jun 16 15:26:06 source-server kernel: NVRM: nvAssertOkFailedNoLog: Assertion failed: Out of memory [NV_ERR_NO_MEMORY] (0x00000051) returned from pRmApi->Alloc(pRmApi, device->session->handle, isSystemMemory ? device->handle : device->subhandle, &physHandle, isSystemMemory ? NV01_MEMORY_SYSTEM : NV01_MEMORY_LOCAL_USER, &memAllocParams, sizeof(memAllocParams)) @ nv_gpu_ops.c:4968
Jun 16 15:45:51 source-server smbd[5622]: [2026/06/16 15:45:51.879326,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 15:45:51 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:34:16 source-server smbd[5622]: [2026/06/16 16:34:16.220110,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:34:16 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:34:16 source-server smbd[5622]: [2026/06/16 16:34:16.360208,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:34:16 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:34:36 source-server smbd[5622]: [2026/06/16 16:34:36.923599,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:34:36 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:34:37 source-server smbd[5622]: [2026/06/16 16:34:37.010934,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:34:37 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:41:24 source-server smbd[5622]: [2026/06/16 16:41:24.712022,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:41:24 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 16:45:36 source-server smbd[5622]: [2026/06/16 16:45:36.731102,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 16:45:36 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:19:26 source-server smbd[5622]: [2026/06/16 17:19:25.863320,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:19:26 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:19:26 source-server smbd[5622]: [2026/06/16 17:19:26.092510,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:19:26 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:25:53 source-server smbd[5622]: [2026/06/16 17:25:53.072953,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:25:53 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:25:53 source-server smbd[5622]: [2026/06/16 17:25:53.263925,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:25:53 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:37:07 source-server smbd[5622]: [2026/06/16 17:37:07.066460,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:37:07 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 17:37:07 source-server smbd[5622]: [2026/06/16 17:37:07.241061,  0] source3/param/loadparm.c:3480(process_usershare_file)
Jun 16 17:37:07 source-server smbd[5622]:   process_usershare_file: stat of /var/lib/samba/usershares/node_modules failed. Permission denied
Jun 16 22:25:02 source-server systemd[1]: casaos.service: Failed with result 'exit-code'.
Jun 16 22:37:44 source-server systemd[1]: casaos.service: Failed with result 'exit-code'.
Jun 17 12:27:25 source-server systemd[1]: casaos.service: Failed with result 'exit-code'.
Jun 17 16:04:51 source-server systemd[1]: casaos.service: Failed with result 'exit-code'.
Jun 17 19:42:26 source-server systemd[1]: casaos.service: Failed with result 'exit-code'.
Jun 17 20:58:20 source-server kernel: python invoked oom-killer: gfp_mask=0x140cca(GFP_HIGHUSER_MOVABLE|__GFP_COMP), order=0, oom_score_adj=0
Jun 17 20:58:21 source-server kernel: CPU: 4 PID: 275224 Comm: python Tainted: G           OE      6.8.0-124-generic #124-Ubuntu
Jun 17 20:58:23 source-server kernel: Hardware name: Dell Inc. Precision Tower 3620/09WH54, BIOS 2.25.0 04/05/2023
Jun 17 20:58:23 source-server kernel: Call Trace:
Jun 17 20:58:23 source-server kernel:  <TASK>
Jun 17 20:58:24 source-server kernel:  dump_stack_lvl+0x76/0xa0
Jun 17 20:58:26 source-server kernel:  dump_stack+0x10/0x20
Jun 17 20:58:27 source-server kernel:  dump_header+0x49/0x210
Jun 17 20:58:28 source-server kernel:  oom_kill_process+0x118/0x280
Jun 17 20:58:30 source-server kernel:  ? oom_evaluate_task+0x143/0x1e0
Jun 17 20:58:30 source-server kernel:  out_of_memory+0x103/0x350
Jun 17 20:58:30 source-server kernel:  __alloc_pages_may_oom+0x10c/0x1d0
Jun 17 20:58:32 source-server kernel:  __alloc_pages_slowpath.constprop.0+0x4c9/0xa50
Jun 17 20:58:33 source-server kernel:  __alloc_pages+0x31f/0x350
Jun 17 20:58:34 source-server kernel:  alloc_pages_mpol+0x91/0x210
Jun 17 20:58:34 source-server kernel:  alloc_pages+0x5b/0xd0
Jun 17 20:58:34 source-server kernel:  folio_alloc+0x15/0x40
Jun 17 20:58:35 source-server kernel:  filemap_alloc_folio+0xf4/0x100
Jun 17 20:58:35 source-server kernel:  __filemap_get_folio+0x199/0x2e0
Jun 17 20:58:35 source-server kernel:  filemap_fault+0x15c/0x8e0
Jun 17 20:58:35 source-server kernel:  ? set_pte_range+0xfd/0x310
Jun 17 20:58:35 source-server kernel:  __do_fault+0x3a/0x190
Jun 17 20:58:35 source-server kernel:  do_read_fault+0x133/0x200
Jun 17 20:58:35 source-server kernel:  do_fault+0xf0/0x260
Jun 17 20:58:36 source-server kernel:  handle_pte_fault+0x114/0x1d0
Jun 17 20:58:36 source-server kernel:  __handle_mm_fault+0x654/0x790
Jun 17 20:58:36 source-server kernel:  handle_mm_fault+0x18a/0x380
Jun 17 20:58:36 source-server kernel:  do_user_addr_fault+0x169/0x670
Jun 17 20:58:36 source-server kernel:  exc_page_fault+0x83/0x1b0
Jun 17 20:58:38 source-server kernel:  asm_exc_page_fault+0x27/0x30
Jun 17 20:58:39 source-server kernel: RIP: 0033:0x7c20097606a0
Jun 17 20:58:40 source-server kernel: Code: Unable to access opcode bytes at 0x7c2009760676.
Jun 17 20:58:41 source-server kernel: RSP: 002b:00007fff9a79bfc8 EFLAGS: 00010202
Jun 17 20:58:41 source-server kernel: RAX: 0000000000000002 RBX: 00007c1febc989c0 RCX: 0000000000000000
Jun 17 20:58:41 source-server kernel: RDX: 0000000000000001 RSI: 00007c1feb5d8f80 RDI: 00007c1febc989c0
Jun 17 20:58:42 source-server kernel: RBP: 0000000000000000 R08: 0000000000000000 R09: 0000000000000000
Jun 17 20:58:42 source-server kernel: R10: 0000000000000000 R11: 000000000d0f9a00 R12: 00007c2009f70f40
Jun 17 20:58:43 source-server kernel: R13: 0000000000a3f8a0 R14: 0000000000000000 R15: 00007c1ff05976f0
Jun 17 20:58:44 source-server kernel:  </TASK>
Jun 17 20:58:44 source-server kernel: Mem-Info:
Jun 17 20:58:44 source-server kernel: active_anon:2192751 inactive_anon:1519972 isolated_anon:0
                                       active_file:330 inactive_file:1865 isolated_file:0
                                       unevictable:6901 dirty:136 writeback:0
                                       slab_reclaimable:109257 slab_unreclaimable:49312
                                       mapped:40829 shmem:37383 pagetables:40779
                                       sec_pagetables:0 bounce:0
                                       kernel_misc_reclaimable:0
                                       free:32756 free_pcp:816 free_cma:0
Jun 17 20:58:44 source-server kernel: Node 0 active_anon:8771004kB inactive_anon:6079888kB active_file:1320kB inactive_file:7460kB unevictable:27604kB isolated(anon):0kB isolated(file):0kB mapped:163316kB dirty:544kB writeback:0kB shmem:149532kB shmem_thp:0kB shmem_pmdmapped:0kB anon_thp:512000kB writeback_tmp:0kB kernel_stack:21120kB pagetables:163116kB sec_pagetables:0kB all_unreclaimable? yes
Jun 17 20:58:44 source-server kernel: Node 0 DMA free:13312kB boost:0kB min:64kB low:80kB high:96kB reserved_highatomic:0KB active_anon:0kB inactive_anon:0kB active_file:0kB inactive_file:0kB unevictable:0kB writepending:0kB present:15988kB managed:15360kB mlocked:0kB bounce:0kB free_pcp:0kB local_pcp:0kB free_cma:0kB
Jun 17 20:58:44 source-server kernel: lowmem_reserve[]: 0 2842 15787 15787 15787
Jun 17 20:58:44 source-server kernel: Node 0 DMA32 free:62516kB boost:0kB min:12156kB low:15192kB high:18228kB reserved_highatomic:0KB active_anon:2138768kB inactive_anon:729756kB active_file:112kB inactive_file:420kB unevictable:0kB writepending:0kB present:3051596kB managed:2985788kB mlocked:0kB bounce:0kB free_pcp:1640kB local_pcp:1640kB free_cma:0kB
Jun 17 20:58:44 source-server kernel: lowmem_reserve[]: 0 0 12944 12944 12944
Jun 17 20:58:44 source-server kernel: Node 0 Normal free:55196kB boost:0kB min:55360kB low:69200kB high:83040kB reserved_highatomic:0KB active_anon:6631804kB inactive_anon:5350564kB active_file:1368kB inactive_file:7092kB unevictable:27604kB writepending:544kB present:13598720kB managed:13263832kB mlocked:27480kB bounce:0kB free_pcp:1624kB local_pcp:500kB free_cma:0kB
Jun 17 20:58:44 source-server kernel: lowmem_reserve[]: 0 0 0 0 0
Jun 17 20:58:46 source-server kernel: Node 0 DMA: 0*4kB 0*8kB 0*16kB 0*32kB 0*64kB 0*128kB 0*256kB 0*512kB 1*1024kB (U) 2*2048kB (UM) 2*4096kB (M) = 13312kB
Jun 17 20:58:49 source-server kernel: Node 0 DMA32: 315*4kB (UE) 474*8kB (UME) 661*16kB (UME) 333*32kB (UME) 191*64kB (UE) 90*128kB (UME) 30*256kB (UME) 6*512kB (ME) 2*1024kB (M) 0*2048kB 0*4096kB = 62828kB
Jun 17 20:58:49 source-server kernel: Node 0 Normal: 1*4kB (U) 1303*8kB (UM) 1995*16kB (UME) 389*32kB (UE) 0*64kB 0*128kB 0*256kB 0*512kB 0*1024kB 0*2048kB 0*4096kB = 54796kB
Jun 17 20:58:49 source-server kernel: Node 0 hugepages_total=0 hugepages_free=0 hugepages_surp=0 hugepages_size=1048576kB
Jun 17 20:58:49 source-server kernel: Node 0 hugepages_total=0 hugepages_free=0 hugepages_surp=0 hugepages_size=2048kB
Jun 17 20:58:53 source-server kernel: 58123 total pagecache pages
Jun 17 20:59:23 source-server kernel: 16353 pages in swap cache
Jun 17 20:59:23 source-server kernel: Free swap  = 12kB
Jun 17 20:59:23 source-server kernel: Total swap = 4194300kB
Jun 17 20:59:23 source-server kernel: 4166576 pages RAM
Jun 17 20:59:23 source-server kernel: 0 pages HighMem/MovableOnly
Jun 17 20:59:23 source-server kernel: 100331 pages reserved
Jun 17 20:59:23 source-server kernel: 0 pages hwpoisoned
Jun 17 20:59:24 source-server kernel: Out of memory: Killed process 3921 (uvicorn) total-vm:9008816kB, anon-rss:1169716kB, file-rss:256kB, shmem-rss:0kB, UID:0 pgtables:10048kB oom_score_adj:0
```

Current boot last 4h warnings:

```
Jun 17 21:09:33 source-server indicator-sound[2192]: volume-control-pulse.vala:741: unable to get pulse unix socket: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name org.PulseAudio1 was not provided by any .service files
Jun 17 21:09:33 source-server indicator-sound[2192]: media-player-list-greeter.vala:55: Unable to get active entry: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name com.canonical.UnityGreeter was not provided by any .service files
Jun 17 21:09:35 source-server indicator-datet[2186]: could not find the desktop file for 'org.gnome.Calendar.desktop'
Jun 17 21:25:25 source-server xfce4-notifyd[13927]: cannot open display:
Jun 17 21:25:25 source-server systemd[2056]: xfce4-notifyd.service: Failed with result 'exit-code'.
Jun 17 21:25:25 source-server systemd[2056]: Failed to start xfce4-notifyd.service - XFCE notifications service.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:32.933640,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.130326,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.274893,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.279635,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.400244,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.404771,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.417973,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.424377,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.560396,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:33 source-server smbd[1888]: [2026/06/17 21:38:33.565901,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:33 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:45 source-server smbd[1888]: [2026/06/17 21:38:45.996079,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:45 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.059576,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.098512,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.122727,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.129576,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.131709,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.157279,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.205008,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.209690,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:46 source-server smbd[1888]: [2026/06/17 21:38:46.218295,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:46 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:56 source-server smbd[1888]: [2026/06/17 21:38:56.928958,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:56 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:56 source-server smbd[1888]: [2026/06/17 21:38:56.942283,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:56 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.003547,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.010986,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.014628,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.073244,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.198531,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.201370,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.298291,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:38:57 source-server smbd[1888]: [2026/06/17 21:38:57.299776,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:38:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.100156,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.129528,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.162583,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.169120,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.191012,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.235162,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.344184,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.350273,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.412148,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:12 source-server smbd[1888]: [2026/06/17 21:39:12.415871,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:12 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.751762,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.782037,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.783708,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.807603,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.846548,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:39:29 source-server smbd[1888]: [2026/06/17 21:39:29.850141,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:39:29 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.796534,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.816050,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.841956,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.859735,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.876164,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.876369,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.896273,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.901258,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.942839,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:37 source-server smbd[1888]: [2026/06/17 21:41:37.969354,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:37 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:45 source-server smbd[1888]: [2026/06/17 21:41:45.454939,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:45 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:45 source-server smbd[1888]: [2026/06/17 21:41:45.472123,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:45 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:45 source-server smbd[1888]: [2026/06/17 21:41:45.508738,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:45 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:45 source-server smbd[1888]: [2026/06/17 21:41:45.523374,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:45 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:57 source-server smbd[1888]: [2026/06/17 21:41:57.538214,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:57 source-server smbd[1888]: [2026/06/17 21:41:57.544875,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:41:57 source-server smbd[1888]: [2026/06/17 21:41:57.598784,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:41:57 source-server smbd[1888]: [2026/06/17 21:41:57.609248,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:41:57 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:42:03 source-server smbd[1888]: [2026/06/17 21:42:03.691018,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:42:03 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:42:03 source-server smbd[1888]: [2026/06/17 21:42:03.697309,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:42:03 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:42:03 source-server smbd[1888]: [2026/06/17 21:42:03.754658,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:42:03 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:42:03 source-server smbd[1888]: [2026/06/17 21:42:03.757466,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:42:03 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.165017,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.173366,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.182627,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.199852,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-454355343-3176600638-1622726219-1008 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.221551,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.230900,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.237148,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:44:19 source-server smbd[1888]: [2026/06/17 21:44:19.259296,  0] source3/smbd/posix_acls.c:2025(create_canon_ace_lists)
Jun 17 21:44:19 source-server smbd[1888]:   create_canon_ace_lists: unable to map SID S-1-5-21-4258706223-659879830-2287457262-2283895837 to uid or gid.
Jun 17 21:47:32 source-server sudo[24502]:   source : a password is required ; PWD=/home/source/SpiritOS ; USER=ollama ; COMMAND=/usr/bin/test -r /mnt/spirit-8tb/ollama-models
Jun 17 21:47:32 source-server sudo[24513]:   source : a password is required ; PWD=/home/source/SpiritOS ; USER=ollama ; COMMAND=/usr/bin/test -w /mnt/spirit-8tb/ollama-models
```

Filtered signals since yesterday:

```
Jun 17 21:09:23 source-server dockerd[2004]: time="2026-06-17T21:09:23.349304730-04:00" level=info msg="CDI directory does not exist, skipping" dir=/var/run/cdi
Jun 17 21:09:23 source-server dockerd[2004]: time="2026-06-17T21:09:23.349345899-04:00" level=info msg="CDI directory does not exist, skipping" dir=/etc/cdi
Jun 17 21:09:23 source-server dockerd[2004]: time="2026-06-17T21:09:23.369950724-04:00" level=info msg="detected 127.0.0.53 nameserver, assuming systemd-resolved, so using resolv.conf: /run/systemd/resolve/resolv.conf"
Jun 17 21:09:27 source-server kernel: audit: type=1400 audit(1781744967.610:133): apparmor="STATUS" operation="profile_load" profile="unconfined" name="docker-default" pid=2146 comm="apparmor_parser"
Jun 17 21:09:27 source-server dockerd[2004]: time="2026-06-17T21:09:27.761753040-04:00" level=info msg="Creating a containerd client" address=/run/containerd/containerd.sock timeout=1m0s
Jun 17 21:09:28 source-server dockerd[2004]: time="2026-06-17T21:09:28.765086544-04:00" level=info msg="Loading containers: start."
Jun 17 21:09:29 source-server dockerd[2004]: time="2026-06-17T21:09:29.375571546-04:00" level=info msg="NRI is disabled"
Jun 17 21:09:29 source-server dockerd[2004]: time="2026-06-17T21:09:29.375649792-04:00" level=info msg="Starting daemon with containerd snapshotter integration enabled"
Jun 17 21:09:29 source-server dockerd[2004]: time="2026-06-17T21:09:29.841650071-04:00" level=info msg="Restoring containers: start."
Jun 17 21:09:31 source-server systemd[2056]: Starting dconf.service - User preferences database...
Jun 17 21:09:31 source-server at-spi-bus-laun[2137]: Failed to register client: GDBus.Error:org.freedesktop.DBus.Error.UnknownMethod: No such method “RegisterClient”
Jun 17 21:09:31 source-server systemd[2056]: Started dconf.service - User preferences database.
Jun 17 21:09:31 source-server systemd[2056]: Started indicator-power.service - Indicator Power.
Jun 17 21:09:31 source-server dockerd[2004]: time="2026-06-17T21:09:31.462278853-04:00" level=error msg="error unmounting container" container=e9a063b5b83ed413332cfd515fb14752dda24a35361143747912f6cef471c70f error="layer not mounted"
Jun 17 21:09:31 source-server dockerd[2004]: time="2026-06-17T21:09:31.470962122-04:00" level=error msg="error unmounting container" container=97882ee7c880d5e349b263f1f5e667843fd01395040ebf79111b9338fe950b73 error="layer not mounted"
Jun 17 21:09:31 source-server dockerd[2004]: time="2026-06-17T21:09:31.674738993-04:00" level=error msg="error unmounting container" container=1c1c012e5446db884aae93e5d39995ad793eab48e54afd8b9eaa575aa6e89546 error="layer not mounted"
Jun 17 21:09:32 source-server dockerd[2004]: time="2026-06-17T21:09:32.035344116-04:00" level=error msg="error unmounting container" container=4955c93c2195fa2b6d79437fd8cb7fdbc5dae7f7a323d428cb0d7e7f211c9a89 error="layer not mounted"
Jun 17 21:09:32 source-server dockerd[2004]: time="2026-06-17T21:09:32.356656076-04:00" level=error msg="error unmounting container" container=dcce797e03cd7d65a82ceceecd644303b42f665f666dad45a54decea6888c70c error="layer not mounted"
Jun 17 21:09:32 source-server dockerd[2004]: time="2026-06-17T21:09:32.569481635-04:00" level=error msg="error unmounting container" container=20ba507f2f53ede7721a4476162d9ce39fa346a287e21ea6584715067603d8e5 error="layer not mounted"
Jun 17 21:09:32 source-server indicator-keybo[2187]: gtk_icon_theme_get_for_screen: assertion 'GDK_IS_SCREEN (screen)' failed
Jun 17 21:09:33 source-server dockerd[2004]: time="2026-06-17T21:09:33.095401861-04:00" level=error msg="error unmounting container" container=892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error="layer not mounted"
Jun 17 21:09:33 source-server NetworkManager[1188]: <info>  [1781744973.6837] agent-manager: agent[b3b3f76a1d66717d,:1.49/org.freedesktop.nm-applet/113]: agent registered
Jun 17 21:09:34 source-server dbus-daemon[935]: [system] Activating via systemd: service name='org.freedesktop.UPower' unit='upower.service' requested by ':1.50' (uid=113 pid=2183 comm="/usr/lib/unity-settings-daemon/unity-settings-daem" label="unconfined")
Jun 17 21:09:34 source-server systemd[1]: Starting upower.service - Daemon for power management...
Jun 17 21:09:35 source-server systemd[1]: var-lib-docker-rootfs-overlayfs-892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e.mount: Deactivated successfully.
Jun 17 21:09:35 source-server dbus-daemon[935]: [system] Successfully activated service 'org.freedesktop.UPower'
Jun 17 21:09:35 source-server systemd[1]: Started upower.service - Daemon for power management.
Jun 17 21:09:36 source-server dockerd[2004]: time="2026-06-17T21:09:36.752141138-04:00" level=info msg="Deleting nftables IPv4 rules" error="exit status 1" output="Error: Could not process rule: No such file or directory\ndelete table ip docker-bridges"
Jun 17 21:09:36 source-server dockerd[2004]: time="2026-06-17T21:09:36.765486799-04:00" level=info msg="Deleting nftables IPv6 rules" error="exit status 1" output="Error: Could not process rule: No such file or directory\ndelete table ip6 docker-bridges"
Jun 17 21:09:37 source-server NetworkManager[1188]: <info>  [1781744977.5297] manager: (br-17c8c82c252d): new Bridge device (/org/freedesktop/NetworkManager/Devices/4)
Jun 17 21:09:37 source-server tailscaled[1436]: router: portUpdate(port=41641, network=udp6)
Jun 17 21:09:37 source-server tailscaled[1436]: router: portUpdate(port=41641, network=udp4)
Jun 17 21:09:37 source-server systemd-networkd[799]: br-17c8c82c252d: Link UP
Jun 17 21:09:37 source-server NetworkManager[1188]: <info>  [1781744977.5630] manager: (br-2862b317b642): new Bridge device (/org/freedesktop/NetworkManager/Devices/5)
Jun 17 21:09:37 source-server systemd-networkd[799]: br-2862b317b642: Link UP
Jun 17 21:09:37 source-server NetworkManager[1188]: <info>  [1781744977.5892] manager: (br-4f57029d52f7): new Bridge device (/org/freedesktop/NetworkManager/Devices/6)
Jun 17 21:09:37 source-server systemd-networkd[799]: br-4f57029d52f7: Link UP
Jun 17 21:09:37 source-server NetworkManager[1188]: <info>  [1781744977.6149] manager: (docker0): new Bridge device (/org/freedesktop/NetworkManager/Devices/7)
Jun 17 21:09:37 source-server avahi-daemon[934]: Joining mDNS multicast group on interface docker0.IPv4 with address 172.17.0.1.
Jun 17 21:09:37 source-server systemd-networkd[799]: docker0: Link UP
Jun 17 21:09:37 source-server avahi-daemon[934]: New relevant interface docker0.IPv4 for mDNS.
Jun 17 21:09:37 source-server avahi-daemon[934]: Registering new address record for 172.17.0.1 on docker0.IPv4.
Jun 17 21:09:38 source-server tailscaled[1436]: LinkChange: major, rebinding: old: interfaces.State{defaultRoute=enp0s31f6 ifs={enp0s31f6:[10.0.0.186/24 2601:cd:c982:e6d0::b2d0/128 2601:cd:c982:e6d0:4a4d:7eff:fee7:d784/64 llu6] tailscale0:[100.111.32.31/32 fd7a:115c:a1e0::f435:201f/128 llu6] br-17c8c82c252d:down} v4=true v6=true} new: interfaces.State{defaultRoute=enp0s31f6 ifs={br-17c8c82c252d:[172.18.0.1/16] br-2862b317b642:[172.20.0.1/16] br-4f57029d52f7:[172.19.0.1/16] docker0:[172.17.0.1/16] enp0s31f6:[10.0.0.186/24 2601:cd:c982:e6d0::b2d0/128 2601:cd:c982:e6d0:4a4d:7eff:fee7:d784/64 llu6] tailscale0:[100.111.32.31/32 fd7a:115c:a1e0::f435:201f/128 llu6]} v4=true v6=true} diff: numInterfaces: 4->7; numInterfaceIPs: 4->7; if br-17c8c82c252d flags: broadcast|multicast->up|broadcast|multicast; if br-2862b317b642: added; if br-4f57029d52f7: added; if docker0: added; ips br-2862b317b642: added [172.20.0.1/16]; ips br-4f57029d52f7: added [172.19.0.1/16]; ips docker0: added [172.17.0.1/16] rebind-reason=[ips-changed]
Jun 17 21:09:38 source-server tailscaled[1436]: router: portUpdate(port=41641, network=udp6)
Jun 17 21:09:38 source-server tailscaled[1436]: router: portUpdate(port=41641, network=udp4)
Jun 17 21:09:39 source-server dockerd[2004]: time="2026-06-17T21:09:39.027655270-04:00" level=info msg="Removing stale sandbox" cid=e9a063b5b83e isRestore=false sid=574b86f95c16
Jun 17 21:09:39 source-server dockerd[2004]: time="2026-06-17T21:09:39.615696006-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:39 source-server systemd[1]: run-docker-netns-574b86f95c16.mount: Deactivated successfully.
Jun 17 21:09:39 source-server dockerd[2004]: time="2026-06-17T21:09:39.944606661-04:00" level=info msg="Removing stale sandbox" cid=1c1c012e5446 isRestore=false sid=a11f3696369d
Jun 17 21:09:40 source-server dockerd[2004]: time="2026-06-17T21:09:40.251130696-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:40 source-server systemd[1]: run-docker-netns-a11f3696369d.mount: Deactivated successfully.
Jun 17 21:09:40 source-server dockerd[2004]: time="2026-06-17T21:09:40.647834261-04:00" level=info msg="Removing stale sandbox" cid=892c03f267e6 isRestore=false sid=c7370a1b05ae
Jun 17 21:09:40 source-server dockerd[2004]: time="2026-06-17T21:09:40.979136394-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:41 source-server systemd[1]: run-docker-netns-c7370a1b05ae.mount: Deactivated successfully.
Jun 17 21:09:41 source-server dockerd[2004]: time="2026-06-17T21:09:41.240948786-04:00" level=info msg="Removing stale sandbox" cid=97882ee7c880 isRestore=false sid=db19605a33b4
Jun 17 21:09:41 source-server dockerd[2004]: time="2026-06-17T21:09:41.614399629-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:41 source-server systemd[1]: run-docker-netns-db19605a33b4.mount: Deactivated successfully.
Jun 17 21:09:41 source-server dockerd[2004]: time="2026-06-17T21:09:41.976045540-04:00" level=info msg="Removing stale sandbox" cid=4955c93c2195 isRestore=false sid=e18fbd377c1e
Jun 17 21:09:42 source-server dockerd[2004]: time="2026-06-17T21:09:42.433953478-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:42 source-server systemd[1]: run-docker-netns-e18fbd377c1e.mount: Deactivated successfully.
Jun 17 21:09:42 source-server dockerd[2004]: time="2026-06-17T21:09:42.737245810-04:00" level=info msg="Removing stale sandbox" cid=dcce797e03cd isRestore=false sid=e36bb0e46732
Jun 17 21:09:43 source-server dockerd[2004]: time="2026-06-17T21:09:43.102397172-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:43 source-server dockerd[2004]: time="2026-06-17T21:09:43.288119533-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:43 source-server systemd[1]: run-docker-netns-e36bb0e46732.mount: Deactivated successfully.
Jun 17 21:09:43 source-server dockerd[2004]: time="2026-06-17T21:09:43.475484399-04:00" level=info msg="Removing stale sandbox" cid=20ba507f2f53 isRestore=false sid=00a115e9ba7e
Jun 17 21:09:43 source-server dockerd[2004]: time="2026-06-17T21:09:43.708378814-04:00" level=warning msg="Failed deleting service host entries to the running container: open : no such file or directory"
Jun 17 21:09:43 source-server systemd[1]: run-docker-netns-00a115e9ba7e.mount: Deactivated successfully.
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356324842-04:00" level=warning msg="error locating sandbox id e18fbd377c1e339801c9202db20a3c98dfc90e3b81ed97e663fb624997aa7ed7: sandbox e18fbd377c1e339801c9202db20a3c98dfc90e3b81ed97e663fb624997aa7ed7 not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356400283-04:00" level=warning msg="error locating sandbox id 574b86f95c16ecfd87469161c3b6e8eb23eb0603ab5d93b1356767549c57e2c9: sandbox 574b86f95c16ecfd87469161c3b6e8eb23eb0603ab5d93b1356767549c57e2c9 not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356433525-04:00" level=warning msg="error locating sandbox id a11f3696369de3830ce4def11ca752e8322350b925ab6b47e3341af503ed6b7f: sandbox a11f3696369de3830ce4def11ca752e8322350b925ab6b47e3341af503ed6b7f not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356462922-04:00" level=warning msg="error locating sandbox id c7370a1b05aec5c4298a4c00fe366ac60f849dd920738548976af5174d668cf9: sandbox c7370a1b05aec5c4298a4c00fe366ac60f849dd920738548976af5174d668cf9 not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356495595-04:00" level=warning msg="error locating sandbox id 00a115e9ba7e878305a2c3b7c59d51ab65d7d97f5e9f3331f2e28420cdc9b1f9: sandbox 00a115e9ba7e878305a2c3b7c59d51ab65d7d97f5e9f3331f2e28420cdc9b1f9 not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356529263-04:00" level=warning msg="error locating sandbox id e36bb0e46732fd9075e6dd51be4bdcd51080fe92c702219228703a0e275585df: sandbox e36bb0e46732fd9075e6dd51be4bdcd51080fe92c702219228703a0e275585df not found"
Jun 17 21:09:44 source-server dockerd[2004]: time="2026-06-17T21:09:44.356559960-04:00" level=warning msg="error locating sandbox id db19605a33b470f0c8efa7b6edfd44c498ab8438a337bddaaf45107bb43a492b: sandbox db19605a33b470f0c8efa7b6edfd44c498ab8438a337bddaaf45107bb43a492b not found"
Jun 17 21:09:48 source-server systemd[1]: Started docker-1c1c012e5446db884aae93e5d39995ad793eab48e54afd8b9eaa575aa6e89546.scope - libcontainer container 1c1c012e5446db884aae93e5d39995ad793eab48e54afd8b9eaa575aa6e89546.
Jun 17 21:09:48 source-server systemd[1]: Started docker-20ba507f2f53ede7721a4476162d9ce39fa346a287e21ea6584715067603d8e5.scope - libcontainer container 20ba507f2f53ede7721a4476162d9ce39fa346a287e21ea6584715067603d8e5.
Jun 17 21:09:48 source-server systemd[1]: Started docker-4955c93c2195fa2b6d79437fd8cb7fdbc5dae7f7a323d428cb0d7e7f211c9a89.scope - libcontainer container 4955c93c2195fa2b6d79437fd8cb7fdbc5dae7f7a323d428cb0d7e7f211c9a89.
Jun 17 21:09:48 source-server systemd[1]: Started docker-97882ee7c880d5e349b263f1f5e667843fd01395040ebf79111b9338fe950b73.scope - libcontainer container 97882ee7c880d5e349b263f1f5e667843fd01395040ebf79111b9338fe950b73.
Jun 17 21:09:48 source-server systemd[1]: Started docker-dcce797e03cd7d65a82ceceecd644303b42f665f666dad45a54decea6888c70c.scope - libcontainer container dcce797e03cd7d65a82ceceecd644303b42f665f666dad45a54decea6888c70c.
Jun 17 21:09:48 source-server systemd[1]: Started docker-e9a063b5b83ed413332cfd515fb14752dda24a35361143747912f6cef471c70f.scope - libcontainer container e9a063b5b83ed413332cfd515fb14752dda24a35361143747912f6cef471c70f.
Jun 17 21:09:48 source-server NetworkManager[1188]: <info>  [1781744988.5269] manager: (veth6e1fbe5): new Veth device (/org/freedesktop/NetworkManager/Devices/8)
Jun 17 21:09:48 source-server systemd-networkd[799]: veth6e1fbe5: Link UP
Jun 17 21:09:48 source-server NetworkManager[1188]: <info>  [1781744988.8956] manager: (vethdba7676): new Veth device (/org/freedesktop/NetworkManager/Devices/9)
Jun 17 21:09:48 source-server systemd-networkd[799]: vethdba7676: Link UP
Jun 17 21:09:48 source-server systemd-networkd[799]: veth6e1fbe5: Gained carrier
Jun 17 21:09:48 source-server systemd-networkd[799]: br-17c8c82c252d: Gained carrier
Jun 17 21:09:48 source-server NetworkManager[1188]: <info>  [1781744988.9541] device (veth6e1fbe5): carrier: link connected
Jun 17 21:09:48 source-server NetworkManager[1188]: <info>  [1781744988.9545] device (br-17c8c82c252d): carrier: link connected
Jun 17 21:09:49 source-server dockerd[2004]: time="2026-06-17T21:09:49.324128339-04:00" level=info msg="sbJoin: gwep4 ''->'b9c41a3a10ab', gwep6 ''->''" eid=b9c41a3a10ab ep=spirit-searxng net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:09:49 source-server NetworkManager[1188]: <info>  [1781744989.3325] manager: (veth0e4ad1f): new Veth device (/org/freedesktop/NetworkManager/Devices/10)
Jun 17 21:09:49 source-server NetworkManager[1188]: <info>  [1781744989.3344] manager: (veth80f8017): new Veth device (/org/freedesktop/NetworkManager/Devices/11)
Jun 17 21:09:49 source-server systemd-networkd[799]: veth0e4ad1f: Link UP
Jun 17 21:09:49 source-server systemd-networkd[799]: veth80f8017: Link UP
Jun 17 21:09:49 source-server systemd-networkd[799]: vethdba7676: Gained carrier
Jun 17 21:09:49 source-server NetworkManager[1188]: <info>  [1781744989.3732] device (vethdba7676): carrier: link connected
Jun 17 21:09:49 source-server dockerd[2004]: time="2026-06-17T21:09:49.867019540-04:00" level=info msg="sbJoin: gwep4 ''->'e47fe7ea134d', gwep6 ''->''" eid=e47fe7ea134d ep=spirit-openedai-speech net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.0313] manager: (veth84b99b0): new Veth device (/org/freedesktop/NetworkManager/Devices/12)
Jun 17 21:09:50 source-server systemd-networkd[799]: veth84b99b0: Link UP
Jun 17 21:09:50 source-server systemd-networkd[799]: br-17c8c82c252d: Gained IPv6LL
Jun 17 21:09:50 source-server systemd-networkd[799]: veth80f8017: Gained carrier
Jun 17 21:09:50 source-server systemd-networkd[799]: veth0e4ad1f: Gained carrier
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.0829] device (veth80f8017): carrier: link connected
Jun 17 21:09:50 source-server systemd-networkd[799]: br-2862b317b642: Gained carrier
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.0834] device (veth0e4ad1f): carrier: link connected
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.0836] device (br-2862b317b642): carrier: link connected
Jun 17 21:09:50 source-server dockerd[2004]: time="2026-06-17T21:09:50.413998893-04:00" level=info msg="sbJoin: gwep4 ''->'97236110c41b', gwep6 ''->''" eid=97236110c41b ep=source-postgres net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:09:50 source-server dockerd[2004]: time="2026-06-17T21:09:50.506255453-04:00" level=info msg="sbJoin: gwep4 ''->'45e415969f1d', gwep6 ''->''" eid=45e415969f1d ep=spirit-jellyfin net=jellyfin_default nid=2862b317b642
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.5948] manager: (veth67115a9): new Veth device (/org/freedesktop/NetworkManager/Devices/13)
Jun 17 21:09:50 source-server systemd-networkd[799]: veth67115a9: Link UP
Jun 17 21:09:50 source-server systemd-networkd[799]: vethdba7676: Gained IPv6LL
Jun 17 21:09:50 source-server systemd-networkd[799]: veth84b99b0: Gained carrier
Jun 17 21:09:50 source-server NetworkManager[1188]: <info>  [1781744990.6251] device (veth84b99b0): carrier: link connected
Jun 17 21:09:50 source-server systemd-networkd[799]: veth6e1fbe5: Gained IPv6LL
Jun 17 21:09:51 source-server dockerd[2004]: time="2026-06-17T21:09:51.003527554-04:00" level=info msg="sbJoin: gwep4 ''->'59cb195c80e2', gwep6 ''->''" eid=59cb195c80e2 ep=scout_v0_1 net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:09:51 source-server systemd-networkd[799]: br-2862b317b642: Gained IPv6LL
Jun 17 21:09:51 source-server systemd-networkd[799]: veth67115a9: Gained carrier
Jun 17 21:09:51 source-server NetworkManager[1188]: <info>  [1781744991.7055] device (veth67115a9): carrier: link connected
Jun 17 21:09:51 source-server systemd-networkd[799]: veth84b99b0: Gained IPv6LL
Jun 17 21:09:51 source-server systemd-networkd[799]: veth80f8017: Gained IPv6LL
Jun 17 21:09:51 source-server systemd-networkd[799]: veth0e4ad1f: Gained IPv6LL
Jun 17 21:09:52 source-server dockerd[2004]: time="2026-06-17T21:09:52.306570076-04:00" level=info msg="sbJoin: gwep4 ''->'d7de234ccd94', gwep6 ''->''" eid=d7de234ccd94 ep=spirit-xtts net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:09:52 source-server NetworkManager[1188]: <info>  [1781744992.3106] manager: (veth533d377): new Veth device (/org/freedesktop/NetworkManager/Devices/14)
Jun 17 21:09:52 source-server systemd-networkd[799]: veth533d377: Link UP
Jun 17 21:09:52 source-server systemd-networkd[799]: veth67115a9: Gained IPv6LL
Jun 17 21:09:53 source-server systemd-networkd[799]: veth533d377: Gained carrier
Jun 17 21:09:53 source-server systemd-networkd[799]: br-4f57029d52f7: Gained carrier
Jun 17 21:09:53 source-server NetworkManager[1188]: <info>  [1781744993.1103] device (veth533d377): carrier: link connected
Jun 17 21:09:53 source-server NetworkManager[1188]: <info>  [1781744993.1108] device (br-4f57029d52f7): carrier: link connected
Jun 17 21:09:53 source-server dockerd[2004]: time="2026-06-17T21:09:53.367533968-04:00" level=info msg="sbJoin: gwep4 '59cb195c80e2'->'59cb195c80e2', gwep6 ''->''" eid=7e62143322d2 ep=scout_v0_1 net=scout_default nid=4f57029d52f7
Jun 17 21:09:53 source-server systemd[1]: Started docker-892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e.scope - libcontainer container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e.
Jun 17 21:09:54 source-server systemd-networkd[799]: veth533d377: Gained IPv6LL
Jun 17 21:09:54 source-server systemd-networkd[799]: br-4f57029d52f7: Gained IPv6LL
Jun 17 21:11:07 source-server NetworkManager[1188]: <info>  [1781745067.6805] manager: (veth706bb93): new Veth device (/org/freedesktop/NetworkManager/Devices/15)
Jun 17 21:11:07 source-server systemd-networkd[799]: veth706bb93: Link UP
Jun 17 21:11:09 source-server systemd-networkd[799]: veth706bb93: Gained carrier
Jun 17 21:11:09 source-server NetworkManager[1188]: <info>  [1781745069.2604] device (veth706bb93): carrier: link connected
Jun 17 21:11:10 source-server dockerd[2004]: time="2026-06-17T21:11:10.259050658-04:00" level=info msg="sbJoin: gwep4 ''->'bd4eac5ce9d3', gwep6 ''->''" eid=bd4eac5ce9d3 ep=spirit-whisper net=backend_spirit-net nid=17c8c82c252d
Jun 17 21:11:10 source-server systemd-networkd[799]: veth706bb93: Gained IPv6LL
Jun 17 21:11:13 source-server dockerd[2004]: time="2026-06-17T21:11:13.778918896-04:00" level=info msg="Loading containers: done."
Jun 17 21:11:14 source-server dockerd[2004]: time="2026-06-17T21:11:14.739234796-04:00" level=info msg="Docker daemon" commit=daa0cb7 containerd-snapshotter=true storage-driver=overlayfs version=29.4.0
Jun 17 21:11:14 source-server dockerd[2004]: time="2026-06-17T21:11:14.855586798-04:00" level=info msg="Initializing buildkit"
Jun 17 21:11:29 source-server dockerd[2004]: time="2026-06-17T21:11:29.819751439-04:00" level=info msg="Completed buildkit initialization"
Jun 17 21:11:29 source-server dockerd[2004]: time="2026-06-17T21:11:29.961811320-04:00" level=info msg="Daemon has completed initialization"
Jun 17 21:11:29 source-server dockerd[2004]: time="2026-06-17T21:11:29.961855635-04:00" level=info msg="API listen on /run/docker.sock"
Jun 17 21:11:29 source-server systemd[1]: Started docker.service - Docker Application Container Engine.
Jun 17 21:11:43 source-server dockerd[2004]: time="2026-06-17T21:11:43.844026624-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:11:43 source-server dockerd[2004]: time="2026-06-17T21:11:43.844036269-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:11:43 source-server dockerd[2004]: time="2026-06-17T21:11:43.845279280-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:11:43 source-server casaos-app-management[6499]: 2026-06-17T21:11:43.934-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.jellyseerr.devices must be a list", "composeFile": "/var/lib/casaos/appstore/default/Apps/Jellyseerr/docker-compose.yaml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:45 source-server casaos-app-management[6499]: 2026-06-17T21:11:45.343-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.medusa.cap_add must be a list", "composeFile": "/var/lib/casaos/appstore/default/Apps/Medusa/docker-compose.yml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:49 source-server systemd[1]: Starting fwupd-refresh.service - Refresh fwupd metadata and update motd...
Jun 17 21:11:55 source-server casaos-app-management[6499]: 2026-06-17T21:11:55.337-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.trilium.cap_add must be a list", "composeFile": "/var/lib/casaos/appstore/default/Apps/Trilium/docker-compose.yaml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:55 source-server casaos-app-management[6499]: 2026-06-17T21:11:55.563-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.twingate-connector.devices must be a list", "composeFile": "/var/lib/casaos/appstore/default/Apps/Twingate/docker-compose.yml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:57 source-server casaos-app-management[6499]: 2026-06-17T21:11:57.223-0400        info        appstore size changed, update app store        {"url": "https://casaos.app/store/main.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 94}
Jun 17 21:11:57 source-server systemd[1]: Starting nvidia-cdi-refresh.service - Refresh NVIDIA CDI specification file...
Jun 17 21:11:57 source-server casaos-app-management[6499]: 2026-06-17T21:11:57.809-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "parsing : yaml: unmarshal errors:\n  line 99: mapping key \"ports\" already defined at line 38\n  line 103: mapping key \"volumes\" already defined at line 56", "composeFile": "/var/lib/casaos/appstore/casaos.app/4e6bf64b187e30664ab8e6ed48331e96/build/sysroot/var/lib/casaos/appstore/default.new/Apps/Etherpad/docker-compose.yml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Ignoring error in locating libnvidia-sandboxutils.so.1: libnvidia-sandboxutils.so.1: not found\nlibnvidia-sandboxutils.so.1: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Failed to init nvsandboxutils: ERROR_LIBRARY_LOAD; ignoring"
Jun 17 21:11:58 source-server casaos-app-management[6499]: 2026-06-17T21:11:58.202-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.psitransfer.ports.0.target must be a integer", "composeFile": "/var/lib/casaos/appstore/casaos.app/4e6bf64b187e30664ab8e6ed48331e96/build/sysroot/var/lib/casaos/appstore/default.new/Apps/PsiTransfer/docker-compose.yml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Using /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Auto-detected mode as 'nvml'"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidia0 as /dev/nvidia0"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/dri/card2 as /dev/dri/card2"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate /dev/dri/controlD66: /dev/dri/controlD66: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/dri/renderD129 as /dev/dri/renderD129"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidia0 as /dev/nvidia0"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/dri/card2 as /dev/dri/card2"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate /dev/dri/controlD66: /dev/dri/controlD66: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/dri/renderD129 as /dev/dri/renderD129"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Using driver version 580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidia-modeset as /dev/nvidia-modeset"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidia-uvm-tools as /dev/nvidia-uvm-tools"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidia-uvm as /dev/nvidia-uvm"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /dev/nvidiactl as /dev/nvidiactl"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-egl-gbm.so.1.1.3 as /usr/lib/x86_64-linux-gnu/libnvidia-egl-gbm.so.1.1.3"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-egl-wayland.so.1.1.13 as /usr/lib/x86_64-linux-gnu/libnvidia-egl-wayland.so.1.1.13"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-allocator.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-allocator.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate libnvidia-vulkan-producer.so.580.159.03: libnvidia-vulkan-producer.so.580.159.03: not found\nlibnvidia-vulkan-producer.so.580.159.03: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/nvidia/xorg/nvidia_drv.so as /usr/lib/x86_64-linux-gnu/nvidia/xorg/nvidia_drv.so"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/nvidia/xorg/libglxserver_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/nvidia/xorg/libglxserver_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/glvnd/egl_vendor.d/10_nvidia.json as /usr/share/glvnd/egl_vendor.d/10_nvidia.json"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/egl/egl_external_platform.d/15_nvidia_gbm.json as /usr/share/egl/egl_external_platform.d/15_nvidia_gbm.json"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/egl/egl_external_platform.d/10_nvidia_wayland.json as /usr/share/egl/egl_external_platform.d/10_nvidia_wayland.json"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/nvidia/nvoptix.bin as /usr/share/nvidia/nvoptix.bin"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/X11/xorg.conf.d/10-nvidia.conf as /usr/share/X11/xorg.conf.d/10-nvidia.conf"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate X11/xorg.conf.d/nvidia-drm-outputclass.conf: X11/xorg.conf.d/nvidia-drm-outputclass.conf: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/vulkan/icd.d/nvidia_icd.json as /etc/vulkan/icd.d/nvidia_icd.json"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate vulkan/icd.d/nvidia_layers.json: vulkan/icd.d/nvidia_layers.json: not found\nvulkan/icd.d/nvidia_layers.json: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/share/vulkan/implicit_layer.d/nvidia_layers.json as /etc/vulkan/implicit_layer.d/nvidia_layers.json"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate vulkan/icd.d/nvidia_icd.x86_64.json: vulkan/icd.d/nvidia_icd.x86_64.json: not found\nvulkan/icd.d/nvidia_icd.x86_64.json: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libGLESv1_CM_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libGLESv1_CM_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libGLESv2_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libGLESv2_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libGLX_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libGLX_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libcuda.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libcuda.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libcudadebugger.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libcudadebugger.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvcuvid.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvcuvid.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-allocator.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-allocator.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-cfg.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-eglcore.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-eglcore.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-fbc.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-fbc.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-glcore.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-glcore.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-glsi.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-glsi.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-glvkspirv.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-glvkspirv.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-gpucomp.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-gpucomp.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-ngx.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-ngx.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-nvvm.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-nvvm.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-opencl.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-opencl.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-opticalflow.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-opticalflow.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-pkcs11-openssl3.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-pkcs11-openssl3.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-pkcs11.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-pkcs11.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-present.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-present.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-ptxjitcompiler.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-ptxjitcompiler.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-rtcore.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-rtcore.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-tls.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-tls.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvidia-vksc-core.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvidia-vksc-core.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/libnvoptix.so.580.159.03 as /usr/lib/x86_64-linux-gnu/libnvoptix.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/lib/x86_64-linux-gnu/vdpau/libvdpau_nvidia.so.580.159.03 as /usr/lib/x86_64-linux-gnu/vdpau/libvdpau_nvidia.so.580.159.03"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /run/nvidia-persistenced/socket as /run/nvidia-persistenced/socket"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate /nvidia-fabricmanager/socket: /nvidia-fabricmanager/socket: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate /tmp/nvidia-mps: /tmp/nvidia-mps: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /lib/firmware/nvidia/580.159.03/gsp_ga10x.bin as /lib/firmware/nvidia/580.159.03/gsp_ga10x.bin"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /lib/firmware/nvidia/580.159.03/gsp_tu10x.bin as /lib/firmware/nvidia/580.159.03/gsp_tu10x.bin"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/bin/nvidia-smi as /usr/bin/nvidia-smi"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/bin/nvidia-debugdump as /usr/bin/nvidia-debugdump"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/bin/nvidia-persistenced as /usr/bin/nvidia-persistenced"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/bin/nvidia-cuda-mps-control as /usr/bin/nvidia-cuda-mps-control"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Selecting /usr/bin/nvidia-cuda-mps-server as /usr/bin/nvidia-cuda-mps-server"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate nvidia-imex: nvidia-imex: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=warning msg="Could not locate nvidia-imex-ctl: nvidia-imex-ctl: not found"
Jun 17 21:11:58 source-server nvidia-ctk[6690]: time="2026-06-17T21:11:58-04:00" level=info msg="Generated CDI spec with version 0.5.0"
Jun 17 21:11:58 source-server systemd[1]: nvidia-cdi-refresh.service: Deactivated successfully.
Jun 17 21:11:58 source-server systemd[1]: Finished nvidia-cdi-refresh.service - Refresh NVIDIA CDI specification file.
Jun 17 21:12:13 source-server dockerd[2004]: time="2026-06-17T21:12:13.897669149-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:12:13 source-server dockerd[2004]: time="2026-06-17T21:12:13.897669229-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:12:13 source-server dockerd[2004]: time="2026-06-17T21:12:13.898774896-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:12:14 source-server fwupd[6675]: 01:12:14.022 FuPluginIntelMe      failed to get public key using /fpf/OemCred: generic failure [0xb]
Jun 17 21:12:14 source-server fwupd[6675]: ERROR:tcti:src/tss2-tcti/tcti-device.c:451:Tss2_Tcti_Device_Init() Failed to open specified TCTI device file /dev/tpmrm0: No such file or directory
Jun 17 21:12:14 source-server casaos-app-management[6499]: 2026-06-17T21:12:14.434-0400        info        appstore size changed, update app store        {"url": "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 94}
Jun 17 21:12:15 source-server casaos-app-management[6499]: 2026-06-17T21:12:15.293-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.redis.healthcheck.retries must be a number", "composeFile": "/var/lib/casaos/appstore/github.com/2a1238d53212bfce4e8f861dcb8ef3fe/big-bear-casaos-master/Apps/ayon/docker-compose.yml", "func": "service.BuildCatalog.func1", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 395}
Jun 17 21:12:16 source-server systemd[1]: Finished fwupd-refresh.service - Refresh fwupd metadata and update motd.
Jun 17 21:12:35 source-server dbus-daemon[935]: [system] Failed to activate service 'org.bluez': timed out (service_start_timeout=25000ms)
Jun 17 21:12:43 source-server dockerd[2004]: time="2026-06-17T21:12:43.951382737-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:12:43 source-server dockerd[2004]: time="2026-06-17T21:12:43.951384006-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:12:43 source-server dockerd[2004]: time="2026-06-17T21:12:43.952547328-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:13:14 source-server dockerd[2004]: time="2026-06-17T21:13:14.022401710-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:13:14 source-server dockerd[2004]: time="2026-06-17T21:13:14.022400030-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:13:14 source-server dockerd[2004]: time="2026-06-17T21:13:14.023871600-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:13:27 source-server casaos[1518]: 2026-06-17T21:13:27.023-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:13:44 source-server dockerd[2004]: time="2026-06-17T21:13:44.090697994-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:13:44 source-server dockerd[2004]: time="2026-06-17T21:13:44.090697992-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:13:44 source-server dockerd[2004]: time="2026-06-17T21:13:44.092120428-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:14:14 source-server dockerd[2004]: time="2026-06-17T21:14:14.157318646-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:14:14 source-server dockerd[2004]: time="2026-06-17T21:14:14.157318283-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:14:14 source-server dockerd[2004]: time="2026-06-17T21:14:14.158549558-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:14:44 source-server dockerd[2004]: time="2026-06-17T21:14:44.221633439-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:14:44 source-server dockerd[2004]: time="2026-06-17T21:14:44.221633446-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:14:44 source-server dockerd[2004]: time="2026-06-17T21:14:44.222843070-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:15:14 source-server dockerd[2004]: time="2026-06-17T21:15:14.292565029-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:15:14 source-server dockerd[2004]: time="2026-06-17T21:15:14.292592866-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:15:14 source-server dockerd[2004]: time="2026-06-17T21:15:14.293601873-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:15:44 source-server dockerd[2004]: time="2026-06-17T21:15:44.390620900-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:15:44 source-server dockerd[2004]: time="2026-06-17T21:15:44.390624704-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:15:44 source-server dockerd[2004]: time="2026-06-17T21:15:44.391891962-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:16:14 source-server dockerd[2004]: time="2026-06-17T21:16:14.478962613-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:16:14 source-server dockerd[2004]: time="2026-06-17T21:16:14.478962492-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:16:14 source-server dockerd[2004]: time="2026-06-17T21:16:14.480247917-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:16:44 source-server dockerd[2004]: time="2026-06-17T21:16:44.528571646-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:16:44 source-server dockerd[2004]: time="2026-06-17T21:16:44.528572112-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:16:44 source-server dockerd[2004]: time="2026-06-17T21:16:44.529633535-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:17:14 source-server dockerd[2004]: time="2026-06-17T21:17:14.606950860-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:17:14 source-server dockerd[2004]: time="2026-06-17T21:17:14.610244249-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:17:14 source-server dockerd[2004]: time="2026-06-17T21:17:14.611756658-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:17:44 source-server dockerd[2004]: time="2026-06-17T21:17:44.715801122-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:17:44 source-server dockerd[2004]: time="2026-06-17T21:17:44.715831993-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:17:44 source-server dockerd[2004]: time="2026-06-17T21:17:44.717076761-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:17:53 source-server casaos-user-service[1543]: [GIN] 2026/06/17 - 21:17:53 | 404 |   26.383416ms |   100.82.31.124 | GET      "/v1/users/image?path=/var/lib/casaos/1/avatar.png"
Jun 17 21:18:14 source-server dockerd[2004]: time="2026-06-17T21:18:14.908371665-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:18:14 source-server dockerd[2004]: time="2026-06-17T21:18:14.908396186-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:18:14 source-server dockerd[2004]: time="2026-06-17T21:18:14.909730158-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:18:32 source-server casaos[1518]: 2026-06-17T21:18:32.011-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:18:45 source-server dockerd[2004]: time="2026-06-17T21:18:45.680242256-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:18:45 source-server dockerd[2004]: time="2026-06-17T21:18:45.680239617-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:18:47 source-server dockerd[2004]: time="2026-06-17T21:18:47.020128416-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:19:17 source-server dockerd[2004]: time="2026-06-17T21:19:17.401506918-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:19:17 source-server dockerd[2004]: time="2026-06-17T21:19:17.401518897-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:19:17 source-server dockerd[2004]: time="2026-06-17T21:19:17.402831102-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:19:47 source-server dockerd[2004]: time="2026-06-17T21:19:47.469852221-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:19:47 source-server dockerd[2004]: time="2026-06-17T21:19:47.470425421-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:19:47 source-server dockerd[2004]: time="2026-06-17T21:19:47.471903214-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:20:17 source-server dockerd[2004]: time="2026-06-17T21:20:17.577514476-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:20:17 source-server dockerd[2004]: time="2026-06-17T21:20:17.577551076-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:20:17 source-server dockerd[2004]: time="2026-06-17T21:20:17.578867947-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:20:47 source-server dockerd[2004]: time="2026-06-17T21:20:47.671683319-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:20:47 source-server dockerd[2004]: time="2026-06-17T21:20:47.671702320-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:20:47 source-server dockerd[2004]: time="2026-06-17T21:20:47.698043014-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:21:17 source-server dockerd[2004]: time="2026-06-17T21:21:17.801760793-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:21:17 source-server dockerd[2004]: time="2026-06-17T21:21:17.801758816-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:21:17 source-server dockerd[2004]: time="2026-06-17T21:21:17.802884410-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:21:47 source-server dockerd[2004]: time="2026-06-17T21:21:47.869176190-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:21:47 source-server dockerd[2004]: time="2026-06-17T21:21:47.869177664-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:21:47 source-server dockerd[2004]: time="2026-06-17T21:21:47.870531979-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:21:57 source-server casaos-app-management[6499]: 2026-06-17T21:21:57.390-0400        info        appstore size not changed        {"url": "https://casaos.app/store/main.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:21:57 source-server casaos-app-management[6499]: 2026-06-17T21:21:57.893-0400        info        appstore size not changed        {"url": "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:22:17 source-server dockerd[2004]: time="2026-06-17T21:22:17.934334076-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:22:17 source-server dockerd[2004]: time="2026-06-17T21:22:17.934342049-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:22:17 source-server dockerd[2004]: time="2026-06-17T21:22:17.935402488-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:22:48 source-server dockerd[2004]: time="2026-06-17T21:22:48.007834295-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:22:48 source-server dockerd[2004]: time="2026-06-17T21:22:48.007866824-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:22:48 source-server dockerd[2004]: time="2026-06-17T21:22:48.033188815-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:23:18 source-server dockerd[2004]: time="2026-06-17T21:23:18.080060711-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:23:18 source-server dockerd[2004]: time="2026-06-17T21:23:18.080061361-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:23:18 source-server dockerd[2004]: time="2026-06-17T21:23:18.105359089-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:23:37 source-server casaos[1518]: 2026-06-17T21:23:37.019-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:23:48 source-server dockerd[2004]: time="2026-06-17T21:23:48.179605552-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:23:48 source-server dockerd[2004]: time="2026-06-17T21:23:48.179627824-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:23:48 source-server dockerd[2004]: time="2026-06-17T21:23:48.180759396-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:24:18 source-server dockerd[2004]: time="2026-06-17T21:24:18.261680494-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:24:18 source-server dockerd[2004]: time="2026-06-17T21:24:18.261709018-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:24:18 source-server dockerd[2004]: time="2026-06-17T21:24:18.263000205-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:24:48 source-server dockerd[2004]: time="2026-06-17T21:24:48.333064222-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:24:48 source-server dockerd[2004]: time="2026-06-17T21:24:48.333081270-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:24:48 source-server dockerd[2004]: time="2026-06-17T21:24:48.364126641-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:25:18 source-server dockerd[2004]: time="2026-06-17T21:25:18.510279073-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:25:18 source-server dockerd[2004]: time="2026-06-17T21:25:18.510281389-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:25:18 source-server dockerd[2004]: time="2026-06-17T21:25:18.511681356-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:25:25 source-server systemd[2056]: xfce4-notifyd.service: Failed with result 'exit-code'.
Jun 17 21:25:25 source-server systemd[2056]: Failed to start xfce4-notifyd.service - XFCE notifications service.
Jun 17 21:25:48 source-server dockerd[2004]: time="2026-06-17T21:25:48.594469294-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:25:48 source-server dockerd[2004]: time="2026-06-17T21:25:48.594503698-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:25:48 source-server dockerd[2004]: time="2026-06-17T21:25:48.595864134-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:26:18 source-server dockerd[2004]: time="2026-06-17T21:26:18.663663946-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:26:18 source-server dockerd[2004]: time="2026-06-17T21:26:18.663663925-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:26:18 source-server dockerd[2004]: time="2026-06-17T21:26:18.664793294-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:26:48 source-server dockerd[2004]: time="2026-06-17T21:26:48.722757700-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:26:48 source-server dockerd[2004]: time="2026-06-17T21:26:48.722757756-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:26:48 source-server dockerd[2004]: time="2026-06-17T21:26:48.723845454-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:27:18 source-server dockerd[2004]: time="2026-06-17T21:27:18.799381682-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:27:18 source-server dockerd[2004]: time="2026-06-17T21:27:18.799381756-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:27:18 source-server dockerd[2004]: time="2026-06-17T21:27:18.800458650-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:27:23 source-server dbus-daemon[2080]: [session uid=113 pid=2080] Failed to activate service 'org.freedesktop.Notifications': timed out (service_start_timeout=120000ms)
Jun 17 21:27:48 source-server dockerd[2004]: time="2026-06-17T21:27:48.885173027-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:27:48 source-server dockerd[2004]: time="2026-06-17T21:27:48.885173477-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:27:48 source-server dockerd[2004]: time="2026-06-17T21:27:48.886485653-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:28:18 source-server dockerd[2004]: time="2026-06-17T21:28:18.998238200-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:28:18 source-server dockerd[2004]: time="2026-06-17T21:28:18.998241908-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:28:18 source-server dockerd[2004]: time="2026-06-17T21:28:18.999430238-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:28:42 source-server casaos[1518]: 2026-06-17T21:28:42.023-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:28:49 source-server dockerd[2004]: time="2026-06-17T21:28:49.078955494-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:28:49 source-server dockerd[2004]: time="2026-06-17T21:28:49.078955496-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:28:49 source-server dockerd[2004]: time="2026-06-17T21:28:49.080096151-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:29:19 source-server dockerd[2004]: time="2026-06-17T21:29:19.142416135-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:29:19 source-server dockerd[2004]: time="2026-06-17T21:29:19.142436857-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:29:19 source-server dockerd[2004]: time="2026-06-17T21:29:19.143462326-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:29:49 source-server dockerd[2004]: time="2026-06-17T21:29:49.208830012-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:29:49 source-server dockerd[2004]: time="2026-06-17T21:29:49.208855497-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:29:49 source-server dockerd[2004]: time="2026-06-17T21:29:49.210128027-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:30:19 source-server dockerd[2004]: time="2026-06-17T21:30:19.301377962-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:30:19 source-server dockerd[2004]: time="2026-06-17T21:30:19.301380198-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:30:19 source-server dockerd[2004]: time="2026-06-17T21:30:19.302649651-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:30:49 source-server dockerd[2004]: time="2026-06-17T21:30:49.367107486-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:30:49 source-server dockerd[2004]: time="2026-06-17T21:30:49.367107837-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:30:49 source-server dockerd[2004]: time="2026-06-17T21:30:49.368177332-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:31:19 source-server dockerd[2004]: time="2026-06-17T21:31:19.436510961-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:31:19 source-server dockerd[2004]: time="2026-06-17T21:31:19.436530829-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:31:19 source-server dockerd[2004]: time="2026-06-17T21:31:19.437717294-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:31:49 source-server dockerd[2004]: time="2026-06-17T21:31:49.496663169-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:31:49 source-server dockerd[2004]: time="2026-06-17T21:31:49.496667906-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:31:49 source-server dockerd[2004]: time="2026-06-17T21:31:49.497792631-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:31:57 source-server casaos-app-management[6499]: 2026-06-17T21:31:57.137-0400        info        appstore size not changed        {"url": "https://casaos.app/store/main.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:31:57 source-server casaos-app-management[6499]: 2026-06-17T21:31:57.478-0400        info        appstore size not changed        {"url": "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:32:19 source-server dockerd[2004]: time="2026-06-17T21:32:19.562825914-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:32:19 source-server dockerd[2004]: time="2026-06-17T21:32:19.562825916-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:32:19 source-server dockerd[2004]: time="2026-06-17T21:32:19.563993698-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:32:49 source-server dockerd[2004]: time="2026-06-17T21:32:49.631892964-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:32:49 source-server dockerd[2004]: time="2026-06-17T21:32:49.631891894-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:32:49 source-server dockerd[2004]: time="2026-06-17T21:32:49.633121961-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:33:19 source-server dockerd[2004]: time="2026-06-17T21:33:19.741613231-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:33:19 source-server dockerd[2004]: time="2026-06-17T21:33:19.741615995-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:33:19 source-server dockerd[2004]: time="2026-06-17T21:33:19.742743169-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:33:47 source-server casaos[1518]: 2026-06-17T21:33:47.023-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:33:49 source-server dockerd[2004]: time="2026-06-17T21:33:49.831246590-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:33:49 source-server dockerd[2004]: time="2026-06-17T21:33:49.831253651-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:33:49 source-server dockerd[2004]: time="2026-06-17T21:33:49.832361054-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:34:19 source-server dockerd[2004]: time="2026-06-17T21:34:19.902528956-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:34:19 source-server dockerd[2004]: time="2026-06-17T21:34:19.902568246-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:34:19 source-server dockerd[2004]: time="2026-06-17T21:34:19.903662604-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:34:49 source-server dockerd[2004]: time="2026-06-17T21:34:49.995678347-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:34:49 source-server dockerd[2004]: time="2026-06-17T21:34:49.995708620-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:34:49 source-server dockerd[2004]: time="2026-06-17T21:34:49.996913353-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:35:20 source-server dockerd[2004]: time="2026-06-17T21:35:20.046468770-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:35:20 source-server dockerd[2004]: time="2026-06-17T21:35:20.046493261-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:35:20 source-server dockerd[2004]: time="2026-06-17T21:35:20.047508435-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:35:50 source-server dockerd[2004]: time="2026-06-17T21:35:50.110051741-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:35:50 source-server dockerd[2004]: time="2026-06-17T21:35:50.110062373-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:35:50 source-server dockerd[2004]: time="2026-06-17T21:35:50.111176876-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:36:20 source-server dockerd[2004]: time="2026-06-17T21:36:20.183826230-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:36:20 source-server dockerd[2004]: time="2026-06-17T21:36:20.183847594-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:36:20 source-server dockerd[2004]: time="2026-06-17T21:36:20.184979295-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:36:50 source-server dockerd[2004]: time="2026-06-17T21:36:50.249116483-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:36:50 source-server dockerd[2004]: time="2026-06-17T21:36:50.249115229-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:36:50 source-server dockerd[2004]: time="2026-06-17T21:36:50.250396464-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:37:20 source-server dockerd[2004]: time="2026-06-17T21:37:20.315471520-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:37:20 source-server dockerd[2004]: time="2026-06-17T21:37:20.315490954-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:37:20 source-server dockerd[2004]: time="2026-06-17T21:37:20.316593030-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:37:50 source-server dockerd[2004]: time="2026-06-17T21:37:50.361715705-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:37:50 source-server dockerd[2004]: time="2026-06-17T21:37:50.361753387-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:37:50 source-server dockerd[2004]: time="2026-06-17T21:37:50.362810541-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:37:57 source-server smartd[964]: Device: /dev/sda [SAT], SMART Usage Attribute: 190 Airflow_Temperature_Cel changed from 65 to 64
Jun 17 21:37:57 source-server smartd[964]: Device: /dev/sda [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 35 to 36
Jun 17 21:37:58 source-server smartd[964]: Device: /dev/sdb [SAT], SMART Usage Attribute: 190 Airflow_Temperature_Cel changed from 65 to 63
Jun 17 21:37:58 source-server smartd[964]: Device: /dev/sdb [SAT], SMART Usage Attribute: 194 Temperature_Celsius changed from 35 to 37
Jun 17 21:38:20 source-server dockerd[2004]: time="2026-06-17T21:38:20.422819732-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:38:20 source-server dockerd[2004]: time="2026-06-17T21:38:20.422836127-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:38:20 source-server dockerd[2004]: time="2026-06-17T21:38:20.423930104-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:38:47 source-server casaos[1518]: 2026-06-17T21:38:47.026-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:38:50 source-server dockerd[2004]: time="2026-06-17T21:38:50.636911904-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:38:50 source-server dockerd[2004]: time="2026-06-17T21:38:50.636915096-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:38:50 source-server dockerd[2004]: time="2026-06-17T21:38:50.638218921-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:39:20 source-server dockerd[2004]: time="2026-06-17T21:39:20.717419265-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:39:20 source-server dockerd[2004]: time="2026-06-17T21:39:20.717467163-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:39:20 source-server dockerd[2004]: time="2026-06-17T21:39:20.795847012-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:39:50 source-server dockerd[2004]: time="2026-06-17T21:39:50.843778234-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:39:50 source-server dockerd[2004]: time="2026-06-17T21:39:50.843778420-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:39:50 source-server dockerd[2004]: time="2026-06-17T21:39:50.845102617-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:40:20 source-server dockerd[2004]: time="2026-06-17T21:40:20.901757675-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:40:20 source-server dockerd[2004]: time="2026-06-17T21:40:20.901778193-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:40:20 source-server dockerd[2004]: time="2026-06-17T21:40:20.902869021-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:40:50 source-server dockerd[2004]: time="2026-06-17T21:40:50.987954180-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:40:50 source-server dockerd[2004]: time="2026-06-17T21:40:50.987969556-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:40:50 source-server dockerd[2004]: time="2026-06-17T21:40:50.989157625-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:41:21 source-server dockerd[2004]: time="2026-06-17T21:41:21.198374861-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:41:21 source-server dockerd[2004]: time="2026-06-17T21:41:21.198412276-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:41:21 source-server dockerd[2004]: time="2026-06-17T21:41:21.199712138-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:41:51 source-server dockerd[2004]: time="2026-06-17T21:41:51.269470507-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:41:51 source-server dockerd[2004]: time="2026-06-17T21:41:51.269471900-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:41:51 source-server dockerd[2004]: time="2026-06-17T21:41:51.270674681-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:41:57 source-server casaos-app-management[6499]: 2026-06-17T21:41:57.157-0400        info        appstore size not changed        {"url": "https://casaos.app/store/main.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:41:57 source-server casaos-app-management[6499]: 2026-06-17T21:41:57.411-0400        info        appstore size not changed        {"url": "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip", "func": "service.(*appStore).UpdateCatalog", "file": "/home/runner/work/CasaOS-AppManagement/CasaOS-AppManagement/service/appstore.go", "line": 91}
Jun 17 21:42:21 source-server dockerd[2004]: time="2026-06-17T21:42:21.361448441-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:42:21 source-server dockerd[2004]: time="2026-06-17T21:42:21.361448474-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:42:21 source-server dockerd[2004]: time="2026-06-17T21:42:21.362690310-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:42:51 source-server dockerd[2004]: time="2026-06-17T21:42:51.416858344-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:42:51 source-server dockerd[2004]: time="2026-06-17T21:42:51.416875471-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:42:51 source-server dockerd[2004]: time="2026-06-17T21:42:51.418225281-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:43:21 source-server dockerd[2004]: time="2026-06-17T21:43:21.480720329-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:43:21 source-server dockerd[2004]: time="2026-06-17T21:43:21.480756010-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:43:21 source-server dockerd[2004]: time="2026-06-17T21:43:21.481763328-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:43:51 source-server dockerd[2004]: time="2026-06-17T21:43:51.527612937-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:43:51 source-server dockerd[2004]: time="2026-06-17T21:43:51.527615650-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:43:51 source-server dockerd[2004]: time="2026-06-17T21:43:51.528702801-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:43:52 source-server casaos[1518]: 2026-06-17T21:43:52.019-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:44:21 source-server dockerd[2004]: time="2026-06-17T21:44:21.615694371-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:44:21 source-server dockerd[2004]: time="2026-06-17T21:44:21.615746893-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:44:21 source-server dockerd[2004]: time="2026-06-17T21:44:21.617076751-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:44:51 source-server dockerd[2004]: time="2026-06-17T21:44:51.693809623-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:44:51 source-server dockerd[2004]: time="2026-06-17T21:44:51.693814996-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:44:51 source-server dockerd[2004]: time="2026-06-17T21:44:51.694993761-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:45:21 source-server dockerd[2004]: time="2026-06-17T21:45:21.771324804-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:45:21 source-server dockerd[2004]: time="2026-06-17T21:45:21.771330128-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:45:21 source-server dockerd[2004]: time="2026-06-17T21:45:21.773504862-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:45:51 source-server dockerd[2004]: time="2026-06-17T21:45:51.825711662-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:45:51 source-server dockerd[2004]: time="2026-06-17T21:45:51.825718265-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:45:51 source-server dockerd[2004]: time="2026-06-17T21:45:51.826901951-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:46:21 source-server dockerd[2004]: time="2026-06-17T21:46:21.937729673-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:46:21 source-server dockerd[2004]: time="2026-06-17T21:46:21.937768235-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:46:21 source-server dockerd[2004]: time="2026-06-17T21:46:21.939097702-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:46:51 source-server dockerd[2004]: time="2026-06-17T21:46:51.987607750-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:46:51 source-server dockerd[2004]: time="2026-06-17T21:46:51.987617640-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:46:51 source-server dockerd[2004]: time="2026-06-17T21:46:51.988848072-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:47:22 source-server dockerd[2004]: time="2026-06-17T21:47:22.049012885-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:47:22 source-server dockerd[2004]: time="2026-06-17T21:47:22.049037607-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:47:22 source-server dockerd[2004]: time="2026-06-17T21:47:22.050087163-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:47:52 source-server dockerd[2004]: time="2026-06-17T21:47:52.151510256-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:47:52 source-server dockerd[2004]: time="2026-06-17T21:47:52.151548617-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:47:52 source-server dockerd[2004]: time="2026-06-17T21:47:52.152868990-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:48:22 source-server dockerd[2004]: time="2026-06-17T21:48:22.404914539-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:48:22 source-server dockerd[2004]: time="2026-06-17T21:48:22.406245438-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:48:22 source-server dockerd[2004]: time="2026-06-17T21:48:22.407536969-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:48:52 source-server casaos[1518]: 2026-06-17T21:48:52.024-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/runner/work/CasaOS/CasaOS/service/system.go", "line": 485}
Jun 17 21:48:52 source-server dockerd[2004]: time="2026-06-17T21:48:52.491758613-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:48:52 source-server dockerd[2004]: time="2026-06-17T21:48:52.491780884-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:48:52 source-server dockerd[2004]: time="2026-06-17T21:48:52.493076603-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:49:22 source-server dockerd[2004]: time="2026-06-17T21:49:22.570857373-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:49:22 source-server dockerd[2004]: time="2026-06-17T21:49:22.570888634-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:49:22 source-server dockerd[2004]: time="2026-06-17T21:49:22.572003131-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:49:52 source-server dockerd[2004]: time="2026-06-17T21:49:52.664557139-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:49:52 source-server dockerd[2004]: time="2026-06-17T21:49:52.664563474-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:49:52 source-server dockerd[2004]: time="2026-06-17T21:49:52.665805158-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:50:22 source-server dockerd[2004]: time="2026-06-17T21:50:22.766772251-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:50:22 source-server dockerd[2004]: time="2026-06-17T21:50:22.766781935-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:50:22 source-server dockerd[2004]: time="2026-06-17T21:50:22.767865885-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:50:52 source-server dockerd[2004]: time="2026-06-17T21:50:52.817115728-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:50:52 source-server dockerd[2004]: time="2026-06-17T21:50:52.817126429-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:50:52 source-server dockerd[2004]: time="2026-06-17T21:50:52.818410187-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.902833853-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stdout
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.902857326-04:00" level=error msg="copy stream failed" error="reading from a closed fifo" stream=stderr
Jun 17 21:51:22 source-server dockerd[2004]: time="2026-06-17T21:51:22.904345409-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH"
```

## Suspicious Signals

See `41-crash-signals.json`. Most relevant keyword counts: {"ata": 147, "docker": 348, "ext4": 6, "failed": 450, "gpu": 20, "killed process": 3, "network": 94, "nvidia": 251, "oom": 22, "out of memory": 9, "power": 52, "reboot": 4, "temperature": 4, "thermal": 60, "watchdog": 1}

## Likely Causes

- Likely cause cannot be stated as proven unless logs show explicit power, thermal, OOM, storage, GPU, or service failure evidence.
- If previous boot journal is truncated or unavailable, host power loss remains possible but unproven.

## Ruled-Out Causes

- Causes with zero matching log evidence in `41-crash-signals.json` are not supported by this audit window.

## Unknowns

- Hardware/power events outside retained journal coverage.
- Thermal sensor history if not logged.
- UPS/power-strip events if external to OS logs.

## Next Commands Requiring Sudo or Approval

- `sudo journalctl -b -1 --no-pager` for fuller previous-boot logs if current user lacks entries.
- Hardware SMART checks such as `sudo smartctl -a <disk>` if Britton approves installing/running disk diagnostics.
- Thermal sensor setup if `sensors` is unavailable.


## Auditor Synthesis

- Confirmed reboot window: `journalctl --list-boots` shows boot `-1` ending at `Wed 2026-06-17 21:00:11 EDT` and boot `0` starting at `Wed 2026-06-17 21:07:20 EDT`.
- Confirmed unclean shutdown signal: current boot warnings include `system.journal corrupted or uncleanly shut down, renaming and replacing` at `Jun 17 21:07:32`.
- Confirmed server-drop signal immediately before the reboot: previous boot logs show `python invoked oom-killer` at `Jun 17 20:58:20` and `Out of memory: Killed process 3921 (uvicorn)` at `Jun 17 20:59:24`.
- Likely runtime impact: the OOM-killed `uvicorn` process is consistent with Source Proxy/backend death just before the host reboot window, but it does not by itself prove the physical shutdown cause.
- Not proven: no kernel panic, segfault, or disk I/O error was found in the filtered window. Thermal entries are mostly sensor discovery/temperature attribute changes, not explicit overheat shutdown evidence.
- Suspicious but secondary: Docker restored stale sandboxes after boot and one container health check repeatedly fails because `curl` is missing in the container image; this is a container health definition problem, not direct proof of the Dell power event.
