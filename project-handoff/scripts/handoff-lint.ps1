# handoff-lint.ps1 - HANDOFF.md budget/structure check + environment fingerprint.
# Platforms: Windows PowerShell 5.1+ / PowerShell 7+. Unix: handoff-lint.sh (same contract).
# ASCII-only on purpose: PS 5.1 reads BOM-less .ps1 as GBK and chokes on CJK bytes.
#
# Usage:
#   handoff-lint.ps1 check [HANDOFF.md]
#   handoff-lint.ps1 fp write [projectDir]
#   handoff-lint.ps1 fp check [projectDir]
#   (bare subcommands only: with -File, "--write" is parsed as a parameter name)
#
# Exit: 0 pass / unchanged; 1 over budget / changed; 2 usage error.

param(
  [Parameter(Position = 0)][string]$Action = 'check',
  [Parameter(Position = 1)][string]$A1 = '',
  [Parameter(Position = 2)][string]$A2 = ''
)

$ErrorActionPreference = 'Stop'
$TokenBudget = 1000
$BytesPerToken = 3

function Get-Utf8Bytes([string]$text) {
  return [System.Text.Encoding]::UTF8.GetByteCount($text)
}

function Get-Sha256Hex([string]$text) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
  return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Get-FileSha256Hex([string]$path) {
  return (Get-FileHash -Algorithm SHA256 -Path $path).Hash.ToLower()
}

function Get-SectionText([string[]]$lines, [int]$n) {
  $out = New-Object System.Collections.Generic.List[string]
  $on = $false
  foreach ($l in $lines) {
    if ($l -match '^## ') {
      $on = ($l -match "^## $n\.")
      continue
    }
    if ($on) { [void]$out.Add($l) }
  }
  return ($out -join "`n")
}

function Invoke-Check([string]$File) {
  if (-not (Test-Path -LiteralPath $File)) { Write-Output "handoff-lint: not found: $File"; exit 2 }
  $text = [System.IO.File]::ReadAllText($File)
  $bytes = Get-Utf8Bytes $text
  $tokens = [math]::Ceiling($bytes / $BytesPerToken)
  $lines = $text -split "`n"
  $fails = 0
  $warns = 0
  Write-Output "HANDOFF: $File"
  Write-Output ("  size: {0} B  ->  ~{1} tokens (bytes/{2})  budget {3}" -f $bytes, $tokens, $BytesPerToken, $TokenBudget)
  if ($tokens -gt $TokenBudget) {
    Write-Output ("  FAIL over budget: {0} > {1}" -f $tokens, $TokenBudget)
    $fails++
  } else {
    Write-Output "  OK   within budget"
  }

  foreach ($n in 1..5) {
    if (-not ($lines | Where-Object { $_ -match "^## $n\." })) {
      Write-Output "  FAIL missing section: ## $n."
      $fails++
    }
  }
  if ($lines | Where-Object { $_ -match '^## 6\.' }) {
    Write-Output "  WARN section ## 6 (maintenance rules) should be deleted"
    $warns++
  }
  $nonstd = $lines | Where-Object { $_ -match '^## ' -and $_ -notmatch '^## [1-5]\.' -and $_ -notmatch '^## 6\.' }
  if ($nonstd) {
    Write-Output "  WARN non-standard section heading(s):"
    $nonstd | ForEach-Object { Write-Output "         $_" }
    $warns++
  }

  $s2 = Get-SectionText $lines 2
  if ($s2 -match '(?m)^- `?[0-9a-f]{7}') {
    Write-Output "  WARN section 2 contains a commit list (redundant with git log)"
    $warns++
  }
  $s1 = Get-SectionText $lines 1
  if ($s1 -match '[\u524d\u4e0a][\u6b21\u4ea4\u63a5]') {
    Write-Output "  WARN section 1 retains prior-handoff history (move to cycles.md)"
    $warns++
  }

  $d = Split-Path -Parent $File
  if ([string]::IsNullOrEmpty($d)) { $d = '.' }
  foreach ($a in 'cycles', 'done', 'pits') {
    if (-not (Test-Path -LiteralPath (Join-Path $d "HANDOFF-ARCHIVE/$a.md"))) {
      Write-Output "  WARN missing HANDOFF-ARCHIVE/$a.md"
      $warns++
    }
  }

  $longn = ($lines | Where-Object { $_.Length -gt 200 }).Count
  if ($longn -gt 0) {
    Write-Output "  WARN $longn line(s) longer than 200 chars"
    $warns++
  }

  Write-Output "  result: $fails fail / $warns warn"
  if ($fails -gt 0) { exit 1 } else { exit 0 }
}

function Invoke-Fp([string]$Mode, [string]$Dir) {
  $Mode = $Mode -replace '^--', ''   # accept both 'write'/'check' and '--write'/'--check'
  $DirFull = (Resolve-Path -LiteralPath $Dir).Path
  $list = Join-Path $DirFull '.handoff/fp.txt'
  $sha = Join-Path $DirFull '.handoff/fp.sha'
  if (-not (Test-Path -LiteralPath $list)) { Write-Output "handoff-lint: missing fingerprint input list: $list"; exit 2 }

  $itemLines = New-Object System.Collections.Generic.List[string]
  Push-Location -LiteralPath $DirFull
  foreach ($raw in [System.IO.File]::ReadAllLines($list)) {
    $line = $raw.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { continue }
    $idx = $line.IndexOf(':')
    if ($idx -lt 1) { continue }
    $kind = $line.Substring(0, $idx)
    $val = $line.Substring($idx + 1)
    $h = ''
    if ($kind -eq 'cmd') {
      $out = ''
      try {
        $prevEA = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $out = (Invoke-Expression $val 2>$null | Out-String)
        $ErrorActionPreference = $prevEA
      } catch { $out = 'ERROR' }
      $h = (Get-Sha256Hex $out).Substring(0, 8)
    } elseif ($kind -eq 'file') {
      $p = Join-Path $DirFull $val
      if (Test-Path -LiteralPath $p) { $h = (Get-FileSha256Hex $p).Substring(0, 8) } else { $h = 'MISSING' }
    } else {
      continue
    }
    $itemLines.Add("$line = $h")
  }
  Pop-Location
  $joined = ($itemLines -join "`n") + "`n"
  $overall = (Get-Sha256Hex $joined).Substring(0, 12)

  if ($Mode -eq 'write') {
    New-Item -ItemType Directory -Force -Path (Join-Path $DirFull '.handoff') | Out-Null
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $content = "fp $overall`nat $stamp`n" + $joined
    [System.IO.File]::WriteAllText($sha, $content)
    Write-Output "fingerprint written: $sha (fp $overall)"
    exit 0
  }

  if (-not (Test-Path -LiteralPath $sha)) { Write-Output "WARN no $sha (run 'fp write' first)"; exit 1 }
  $prevLines = [System.IO.File]::ReadAllLines($sha)
  $prev = ($prevLines[0] -split '\s+')[1]
  if ($prev -eq $overall) {
    Write-Output "OK env unchanged (fp $overall) - skip environment re-verification"
    exit 0
  }
  Write-Output "CHANGED env (fp $prev -> $overall) - re-verify only changed items:"
  $prevItems = @()
  if ($prevLines.Count -gt 2) { $prevItems = $prevLines[2..($prevLines.Count - 1)] }
  Compare-Object $prevItems ($itemLines.ToArray()) | ForEach-Object {
    Write-Output ("    {0} {1}" -f $_.SideIndicator, $_.InputObject)
  }
  exit 1
}

switch ($Action) {
  'check' {
    $f = if ($A1) { $A1 } else { 'HANDOFF.md' }
    Invoke-Check $f
  }
  'fp' {
    $m = if ($A1) { $A1 } else { 'check' }
    $d = if ($A2) { $A2 } else { '.' }
    Invoke-Fp $m $d
  }
  default {
    Write-Output 'usage: handoff-lint.ps1 {check [HANDOFF.md] | fp write|check [projectDir]}'
    exit 2
  }
}
