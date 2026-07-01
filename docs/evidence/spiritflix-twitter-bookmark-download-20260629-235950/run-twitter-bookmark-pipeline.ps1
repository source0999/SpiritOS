$ErrorActionPreference = 'Continue'
$started = Get-Date -Format o
"STARTED $started" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8
"Existing archive IDs: 857" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8 -Append
"Bookmark URL count: $((Get-Content -LiteralPath 'M:\tempTwitter\bookmarksList.txt' | Where-Object { $_ -match '^https?://' }).Count)" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8 -Append
& yt-dlp --cookies-from-browser chrome --ignore-errors --continue --no-overwrites --retries 3 --fragment-retries 3 --sleep-requests 1 --sleep-interval 1 --max-sleep-interval 4 --download-archive 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\yt-dlp-download-archive.txt' -a 'M:\tempTwitter\bookmarksList.txt' -o 'M:\tempTwitter\%(uploader|unknown)s - %(title).160B [%(id)s].%(ext)s' --merge-output-format mp4 --remux-video mp4 *>> 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log'
$downloadExit = $LASTEXITCODE
"YTDLP_EXIT $downloadExit" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8 -Append
& ssh source@10.0.0.186 "cd /home/source/SpiritOS && node scripts/spiritflix-twitter-intake.mjs --evidence-dir 'docs/evidence/spiritflix-twitter-intake-bookmark-run-20260629-235950' --stable-seconds 120 --rescan-passes 2" *>> 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log'
$intakeExit = $LASTEXITCODE
"INTAKE_EXIT $intakeExit" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8 -Append
"COMPLETED $(Get-Date -Format o)" | Out-File -LiteralPath 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\pipeline.log' -Encoding UTF8 -Append
@{ started = $started; completed = (Get-Date -Format o); downloadExit = $downloadExit; intakeExit = $intakeExit; evidence = 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950'; archive = 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950\yt-dlp-download-archive.txt'; intakeEvidence = 'docs/evidence/spiritflix-twitter-intake-bookmark-run-20260629-235950' } | ConvertTo-Json | Out-File -LiteralPath (Join-Path 'Z:\docs\evidence\spiritflix-twitter-bookmark-download-20260629-235950' 'pipeline-status.json') -Encoding UTF8
