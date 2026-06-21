# Phase 7 Mac Optimizer Readiness

- Mac host reachable: yes
- Mac SSH alias: `spirit-mac-mini`
- Mac status command exit: 0
- ffmpeg on Mac: yes, `/usr/local/bin/ffmpeg`
- ffprobe on Mac: yes, `/usr/local/bin/ffprobe`
- VideoToolbox H.264 encoder available: yes
- x264 fallback available: yes
- Mac direct `/mnt/spirit-8tb` read/write: no; workflow uses Dell-to-Mac `scp` source copy and Mac-to-Dell `scp` output return.
- Output root: `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized`
- Dell can read outputs/receipts: yes, verified after completed jobs.

```text
spirit-mac-mini.local
spiritmac
Darwin spirit-mac-mini.local 24.6.0 Darwin Kernel Version 24.6.0: Tue Apr 21 20:17:54 PDT 2026; root:xnu-11417.140.69.710.16~1/RELEASE_X86_64 x86_64
ffmpeg version 8.1.1 Copyright (c) 2000-2026 the FFmpeg developers
built with Apple clang version 16.0.0 (clang-1600.0.26.6)
configuration: --prefix=/usr/local/Cellar/ffmpeg/8.1.1 --enable-shared --enable-pthreads --enable-version3 --cc=clang --host-cflags= --host-ldflags= --enable-ffplay --enable-gpl --enable-libsvtav1 --enable-libopus --enable-libx264 --enable-libmp3lame --enable-libdav1d --enable-libvmaf --enable-libvpx --enable-libx265 --enable-openssl --enable-videotoolbox --enable-audiotoolbox
libavutil      60. 26.101 / 60. 26.101
libavcodec     62. 28.101 / 62. 28.101
libavformat    62. 12.101 / 62. 12.101
libavdevice    62.  3.101 / 62.  3.101
libavfilter    11. 14.101 / 11. 14.101
libswscale      9.  5.101 /  9.  5.101
libswresample   6.  3.101 /  6.  3.101

Exiting with exit code 0
ffprobe version 8.1.1 Copyright (c) 2007-2026 the FFmpeg developers
built with Apple clang version 16.0.0 (clang-1600.0.26.6)
configuration: --prefix=/usr/local/Cellar/ffmpeg/8.1.1 --enable-shared --enable-pthreads --enable-version3 --cc=clang --host-cflags= --host-ldflags= --enable-ffplay --enable-gpl --enable-libsvtav1 --enable-libopus --enable-libx264 --enable-libmp3lame --enable-libdav1d --enable-libvmaf --enable-libvpx --enable-libx265 --enable-openssl --enable-videotoolbox --enable-audiotoolbox
libavutil      60. 26.101 / 60. 26.101
libavcodec     62. 28.101 / 62. 28.101
libavformat    62. 12.101 / 62. 12.101
libavdevice    62.  3.101 / 62.  3.101
libavfilter    11. 14.101 / 11. 14.101
libswscale      9.  5.101 /  9.  5.101
libswresample   6.  3.101 /  6.  3.101

```
