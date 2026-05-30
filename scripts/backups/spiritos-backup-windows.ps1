param(
  [switch]$DryRun = $true,
  [switch]$Real
)

$ErrorActionPreference = "Stop"

if ($Real) {
  if ($env:SPIRIT_BACKUP_MODE -ne "real" -or $env:SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES -ne "true") {
    throw "APPROVAL REQUIRED: refusing real Windows backup without explicit approval env."
  }
  $DryRun = $false
}

$BackupPaths = @(
  "C:\Projects",
  "C:\Users\smith\OneDrive\Documents\spiritAgent"
)
$ResticRepository = if ($env:RESTIC_REPOSITORY) { $env:RESTIC_REPOSITORY } else { "/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows" }

Write-Output "SpiritOS Windows backup planner"
Write-Output "DryRun=$DryRun"
Write-Output "Scope=$($BackupPaths -join '; ')"
Write-Output "RESTIC_REPOSITORY=$ResticRepository"
Write-Output "This planner is scoped to approved SpiritOS Windows project paths only."
Write-Output "It does not browse the entire Windows machine, copy files, install restic, or print token/secret contents."

$Command = @(
  "restic",
  "-r", $ResticRepository,
  "backup",
  "--exclude", "node_modules",
  "--exclude", ".next",
  "--exclude", "dist"
) + $BackupPaths

if ($DryRun) {
  Write-Output ("[DRY-RUN] " + ($Command -join " "))
} else {
  throw "APPROVAL REQUIRED: real execution intentionally not implemented in v0.1 planner."
}
