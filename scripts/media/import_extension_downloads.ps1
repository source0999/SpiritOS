param(
  [string]$DownloadDir = "$env:USERPROFILE\Downloads",
  [string]$Series = "Rurouni Kenshin (1996)",
  [int]$Season = 1,
  [string]$Remote = "source@10.0.0.186",
  [string]$RemoteInboxRoot = "/mnt/spirit-8tb/media-inbox/anime",
  [string]$FilePattern = "*Hianime*.mp4",
  [int]$OnlyEpisode = 0,
  [switch]$DeleteAfterImport,
  [switch]$Watch,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$videoExtensions = @(".mp4", ".mkv", ".webm", ".m4v", ".mov")
$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

function ConvertTo-SafeRemoteSegment {
  param([string]$Value)
  $clean = $Value -replace '[<>:"/\\|?*\x00-\x1f]+', ''
  $clean = $clean -replace '\s+', ' '
  $clean = $clean.Trim(' ', '.')
  if (-not $clean) { return "untitled" }
  return $clean
}

function Get-EpisodeNumber {
  param([string]$Name)
  $patterns = @(
    'Episode\s+(\d+)',
    '\bEp(?:isode)?[ ._-]*(\d+)\b',
    '\bS\d{1,2}E(\d{1,3})\b'
  )
  foreach ($pattern in $patterns) {
    $match = [regex]::Match($Name, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($match.Success) { return [int]$match.Groups[1].Value }
  }
  return $null
}

function Wait-FileStable {
  param([System.IO.FileInfo]$File)
  $lastLength = -1
  for ($i = 0; $i -lt 8; $i++) {
    $current = Get-Item -LiteralPath $File.FullName -ErrorAction SilentlyContinue
    if (-not $current) {
      Write-Host "Skipped disappearing partial file: $($File.FullName)"
      return $null
    }
    if ($current.Length -eq $lastLength -and $current.Length -gt 0) {
      return $current
    }
    $lastLength = $current.Length
    Start-Sleep -Seconds 2
  }
  throw "File did not become stable: $($File.FullName)"
}

function Import-ExtensionFile {
  param([System.IO.FileInfo]$File)

  if ($File.Name -match '\.(crdownload|part|tmp)$') { return }
  if ($videoExtensions -notcontains $File.Extension.ToLowerInvariant()) { return }
  if (-not $seen.Add($File.FullName)) { return }

  $stableFile = Wait-FileStable -File $File
  if (-not $stableFile) { return }
  $episode = Get-EpisodeNumber -Name $stableFile.Name
  if ($null -eq $episode) {
    Write-Warning "Could not parse episode number from: $($stableFile.Name)"
    return
  }
  if ($OnlyEpisode -gt 0 -and $episode -ne $OnlyEpisode) {
    Write-Host "Skipping episode $episode because -OnlyEpisode $OnlyEpisode is set."
    return
  }

  $safeSeries = ConvertTo-SafeRemoteSegment $Series
  $seasonDir = "Season {0:D2}" -f $Season
  $targetName = "{0} - S{1:D2}E{2:D2}{3}" -f $safeSeries, $Season, $episode, $stableFile.Extension.ToLowerInvariant()
  $remoteDir = "$RemoteInboxRoot/$safeSeries/$seasonDir"
  $remoteFinal = "$remoteDir/$targetName"
  $remoteStageDir = "/mnt/spirit-8tb/media-processing/extension-import-stage"
  $remoteStage = "$remoteStageDir/$targetName"

  Write-Host "Importing $($stableFile.Name) -> $remoteFinal"
  if ($DryRun) { return }

  ssh $Remote "mkdir -p '$remoteDir' '$remoteStageDir'"
  scp "$($stableFile.FullName)" "$Remote`:$remoteStage"
  ssh $Remote "mv -f '$remoteStage' '$remoteFinal'"
  if ($DeleteAfterImport) {
    Remove-Item -LiteralPath $stableFile.FullName -Force
    Write-Host "Deleted local Windows copy: $($stableFile.FullName)"
  }
}

function Scan-Once {
  $files = Get-ChildItem -LiteralPath $DownloadDir -File -Filter $FilePattern -ErrorAction Stop |
    Sort-Object LastWriteTime
  foreach ($file in $files) {
    Import-ExtensionFile -File $file
  }
}

Write-Host "Watching extension downloads in $DownloadDir for $FilePattern"
Write-Host "Target series: $Series / Season $("{0:D2}" -f $Season)"
if ($OnlyEpisode -gt 0) { Write-Host "Only importing episode $OnlyEpisode" }
if ($DeleteAfterImport) { Write-Host "Deleting local file after successful Dell handoff" }

Scan-Once

if ($Watch) {
  while ($true) {
    Start-Sleep -Seconds 5
    Scan-Once
  }
}
