# experiment.ps1 - experimental-handoff isolation helper (init / close / list).
# Platforms: Windows PowerShell 5.1+ / PowerShell 7+. Unix: experiment.sh (same behaviour).
# Encoding: UTF-8 WITH BOM on purpose (PS 5.1 reads BOM-less .ps1 as GBK and chokes on CJK).
#
# Usage (positional; leading-dash options are parsed as parameter NAMES under -File):
#   experiment.ps1 init  <slug> [title] [mode] [base]
#   experiment.ps1 close <slug> keep|discard [paths]
#   experiment.ps1 list  [write]
#
# Isolation auto-chosen: git repo -> worktree (default) or branch (mode=branch); else copy.
# Doc: <proj>/.experiments/<slug>.md (local, gitignored).

param(
  [Parameter(Position = 0)][string]$Cmd = '',
  [Parameter(Position = 1)][string]$Slug = '',
  [Parameter(Position = 2)][string]$Opt1 = '',
  [Parameter(Position = 3)][string]$Opt2 = '',
  [Parameter(Position = 4)][string]$Opt3 = ''
)

$ErrorActionPreference = 'Continue'
$script:Root = (Get-Location).Path
# Keep the process CWD in sync: .NET APIs and native tools (git/tar) use it, NOT PS location.
try { [Environment]::CurrentDirectory = $script:Root } catch { }
$script:U8 = New-Object System.Text.UTF8Encoding($false)

function Die([string]$m) { Write-Output "experiment: $m"; exit 1 }
function Has-Git { return [bool](Get-Command git -ErrorAction SilentlyContinue) }
function Is-Git { if (-not (Has-Git)) { return $false }; & git rev-parse --is-inside-work-tree *> $null; return ($LASTEXITCODE -eq 0) }
function Today { (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd') }
function Read-Text([string]$p) { return [System.IO.File]::ReadAllText($p) }
function Write-Doc([string]$p, [string]$t) { [System.IO.File]::WriteAllText($p, $t, $script:U8) }
function Exp-Dir { return (Join-Path $script:Root '.experiments') }

function Doc-Field([string]$path, [string]$key) {
  $m = [regex]::Match((Read-Text $path), "(?m)^- " + [regex]::Escape($key) + ": (.*)$")
  if ($m.Success) { return $m.Groups[1].Value } else { return '' }
}
function Iso-Part([string]$path, [int]$idx) {
  $m = [regex]::Match((Read-Text $path), "(?m)^- 隔离: (.*)$")
  if (-not $m.Success) { return '' }
  $parts = $m.Groups[1].Value -split ' · '
  if ($idx -lt $parts.Count) { return $parts[$idx] } else { return '' }
}
function Iso-Mode([string]$p) { return (Iso-Part $p 0).Trim() }
function Iso-Loc([string]$p) { return (Iso-Part $p 1) -replace '^位置:\s*', '' }
function Iso-Branch([string]$p) { return (Iso-Part $p 2) -replace '^分支:\s*', '' }

function Write-Index {
  $dir = Exp-Dir
  if (-not (Test-Path $dir)) { return }
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('# 实验索引（自动生成——勿手改）')
  $lines.Add('')
  $lines.Add('| slug | 状态 | 隔离 | 位置/分支 | 日期 | 文档 |')
  $lines.Add('|------|------|------|-----------|------|------|')
  foreach ($f in Get-ChildItem (Join-Path $dir '*.md') -ErrorAction SilentlyContinue) {
    if ($f.Name -eq 'EXPERIMENTS.md') { continue }
    $s = [IO.Path]::GetFileNameWithoutExtension($f.Name)
    $st = Doc-Field $f.FullName '状态'; $m = Iso-Mode $f.FullName
    $l = Iso-Loc $f.FullName; $b = Iso-Branch $f.FullName; $d = Doc-Field $f.FullName '日期'
    $loc = if ($b -and $b -ne '-') { "$l / $b" } else { $l }
    $lines.Add("| $s | $st | $m | $loc | $d | [$s.md]($s.md) |")
  }
  $archDir = Join-Path $dir 'archive'
  if (Test-Path $archDir) {
    foreach ($f in Get-ChildItem (Join-Path $archDir '*.md') -ErrorAction SilentlyContinue) {
      $s = [IO.Path]::GetFileNameWithoutExtension($f.Name)
      $st = Doc-Field $f.FullName '状态'; $d = Doc-Field $f.FullName '日期'
      $lines.Add("| $s | $st | — | 已归档 | $d | [archive/$s.md](archive/$s.md) |")
    }
  }
  Write-Doc (Join-Path $dir 'EXPERIMENTS.md') (($lines -join "`n") + "`n")
}

function Cmd-Init {
  $slug = $Slug; $title = $Opt1; $mode = $Opt2; $base = $Opt3
  if (-not $slug) { Die 'init needs <slug>' }
  if ($slug -notmatch '^[a-z0-9][a-z0-9-]*$') { Die 'slug must match [a-z0-9-] (lowercase)' }
  $root = $script:Root
  $proj = Split-Path -Leaf $root
  $expDir = Exp-Dir
  $docPath = Join-Path $expDir "$slug.md"
  if (Test-Path $docPath) { Die "experiment '$slug' already exists" }

  if (-not $mode) { if (Is-Git) { $mode = 'worktree' } else { $mode = 'copy' } }
  if ($mode -ne 'copy' -and -not (Has-Git)) { Write-Output 'experiment: git not found on PATH - falling back to copy'; $mode = 'copy' }
  $hasHead = $false
  if (Has-Git) { & git rev-parse HEAD *> $null; $hasHead = ($LASTEXITCODE -eq 0) }
  if ($mode -ne 'copy' -and -not $hasHead) { $mode = 'copy' }

  $loc = ''; $br = ''; $basehash = ''
  switch ($mode) {
    'worktree' {
      $loc = "../$proj-exp-$slug"; $br = "exp/$slug"
      if (-not $base) { $base = 'HEAD' }
      $basehash = (& git rev-parse --short $base)
      if (Test-Path (Join-Path (Split-Path $root) "$proj-exp-$slug")) { Die "path exists: $loc" }
      & git worktree add -b $br $loc $base *> $null
      if ($LASTEXITCODE -ne 0) { Die 'git worktree add failed' }
    }
    'branch' {
      $br = "exp/$slug"
      if ((& git status --porcelain)) { Die 'working tree not clean - commit/stash first (or mode=worktree)' }
      if (-not $base) { $base = 'HEAD' }
      $basehash = (& git rev-parse --short $base)
      & git switch -c $br *> $null
      if ($LASTEXITCODE -ne 0) { Die 'git switch failed' }
      $loc = '(in place)'
    }
    'copy' {
      $loc = "../$proj-exp-$slug"; $br = '-'
      $dst = Join-Path (Split-Path $root) "$proj-exp-$slug"
      if (Test-Path $dst) { Die "path exists: $loc" }
      New-Item -ItemType Directory -Force -Path $dst | Out-Null
      $tar = Get-Command tar -ErrorAction SilentlyContinue
      if ($tar) {
        $tmp = Join-Path $env:TEMP ("exp-$slug-" + [guid]::NewGuid().ToString('N') + '.tar')
        & tar -cf $tmp --exclude=./node_modules --exclude=./dist --exclude=./.venv --exclude=./target --exclude=./.next --exclude=./.git --exclude=./.experiments -C $root . *> $null
        & tar -xf $tmp -C $dst *> $null
        $basehash = (Get-FileHash $tmp -Algorithm SHA256).Hash.Substring(0, 12).ToLower()
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
      } else {
        Copy-Item -Path (Join-Path $root '*') -Destination $dst -Recurse -Force
        foreach ($x in 'node_modules', 'dist', '.venv', 'target', '.next', '.git', '.experiments') {
          Remove-Item (Join-Path $dst $x) -Recurse -Force -ErrorAction SilentlyContinue
        }
        $basehash = 'copy'
      }
    }
    default { Die "bad mode: $mode" }
  }

  New-Item -ItemType Directory -Force -Path $expDir | Out-Null
  $gi = Join-Path $root '.gitignore'
  if ((Is-Git) -and (Test-Path $gi)) {
    if (-not (Select-String -Path $gi -Pattern '^\.experiments/$' -Quiet)) { Add-Content -Path $gi -Value '.experiments/' }
  }
  $clean = if ($mode -eq 'copy') { "rm -rf $loc" } else { "git worktree remove $loc ; git branch -d $br" }
  $doc = @"
# Experiment: $slug

- 状态: open
- 日期: $(Today)
- 标题: $(if ($title) { $title } else { $slug })
- Goal: $(if ($title) { $title } else { '<问题/假设>' })
- Method: <方法>
- 隔离: $mode · 位置: $loc · 分支: $br
- 基线: $basehash
- Run: <命令>
- 结论:
- Next Steps:
- 合并计划: 全量
- 合并结果:
- 清理: $clean

## Evidence

（追加式记录测试/指标/观察）
"@
  Write-Doc $docPath $doc
  Write-Index
  Write-Output "experiment '$slug' opened"
  Write-Output "  mode : $mode"
  Write-Output "  loc  : $loc  branch: $br  base: $basehash"
  Write-Output "  doc  : .experiments/$slug.md"
  if ($mode -eq 'worktree') { Write-Output "  next : cd $loc and install deps (worktrees have no node_modules)" }
}

function Cmd-Close {
  $slug = $Slug; $action = $Opt1; $paths = $Opt2
  if (-not $slug) { Die 'close needs <slug>' }
  if ($action -ne 'keep' -and $action -ne 'discard') { Die 'close needs keep|discard' }
  $root = $script:Root
  $expDir = Exp-Dir
  $doc = Join-Path $expDir "$slug.md"
  if (-not (Test-Path $doc)) { Die "not found: .experiments/$slug.md" }
  $mode = Iso-Mode $doc; $loc = Iso-Loc $doc; $br = Iso-Branch $doc
  $overall = 'none'

  if ($action -eq 'keep') {
    if ($mode -eq 'worktree' -or $mode -eq 'branch') {
      if (-not (Has-Git)) { Die "git not found on PATH (needed for $mode close)" }
      if (-not (Is-Git)) { Die "doc says $mode but not a git repo" }
      if ($paths) {
        $pl = $paths -split ','
        & git checkout $br -- @pl
        if ($LASTEXITCODE -ne 0) { Die 'path checkout failed' }
        $overall = "partial: $paths"
      } else {
        & git merge --no-ff $br -m "merge experiment $slug" *> $null
        if ($LASTEXITCODE -ne 0) { Die 'merge failed (resolve conflicts then re-run)' }
        $overall = (& git rev-parse --short HEAD)
      }
    } elseif ($mode -eq 'copy') {
      if (-not (Has-Git)) { Die 'git not found; use Git Bash / WSL experiment.sh to generate the patch' }
      $patch = Join-Path $expDir "$slug.patch"
      $proj = Split-Path -Leaf $root
      $parent = Split-Path $root
      $txt = (& git -C $parent diff --no-index --no-color $proj "$proj-exp-$slug" 2>$null | Out-String)
      if ([string]::IsNullOrWhiteSpace($txt)) { Die "no diff produced - inspect $loc manually" }
      Write-Doc $patch $txt
      $overall = "patch: .experiments/$slug.patch (apply from project root: git apply -p2)"
      Write-Output "experiment: patch written -> .experiments/$slug.patch (review then apply)"
    } else { Die "unknown isolation mode: $mode" }
  }

  switch ($mode) {
    'worktree' { if (Has-Git) { & git worktree remove --force $loc *> $null; & git worktree prune *> $null; & git branch -D $br *> $null } }
    'branch' { if (Has-Git) { & git switch - *> $null; & git branch -D $br *> $null } }
    'copy' {
      $dst = Join-Path (Split-Path $root) "$(Split-Path -Leaf $root)-exp-$slug"
      Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue
    }
  }

  $status = if ($action -eq 'keep') { 'promoted' } else { 'discarded' }
  $t = Read-Text $doc
  $t = [regex]::Replace($t, '(?m)^- 状态:.*$', "- 状态: $status")
  $t = [regex]::Replace($t, '(?m)^- 合并结果:.*$', "- 合并结果: $overall")
  Write-Doc $doc $t
  $archDir = Join-Path $expDir 'archive'
  New-Item -ItemType Directory -Force -Path $archDir | Out-Null
  Move-Item $doc (Join-Path $archDir "$slug.md") -Force
  Write-Index
  Write-Output "experiment '$slug' closed: $status (merge: $overall)"
  Write-Output "  archived: .experiments/archive/$slug.md  sandbox removed: $loc"
}

function Cmd-List {
  $dir = Exp-Dir
  if (-not (Test-Path $dir)) { Write-Output 'no .experiments/'; return }
  if ($Opt1 -eq 'write') { Write-Index }
  Write-Output 'active experiments:'
  $n = 0
  foreach ($f in Get-ChildItem (Join-Path $dir '*.md') -ErrorAction SilentlyContinue) {
    if ($f.Name -eq 'EXPERIMENTS.md') { continue }
    $n++
    $s = [IO.Path]::GetFileNameWithoutExtension($f.Name)
    Write-Output ("  {0,-20} {1,-12} {2}" -f $s, (Doc-Field $f.FullName '状态'), (Doc-Field $f.FullName '日期'))
  }
  if ($n -eq 0) { Write-Output '  (none)' }
  $arch = 0
  $archDir = Join-Path $dir 'archive'
  if (Test-Path $archDir) { $arch = @(Get-ChildItem (Join-Path $archDir '*.md') -ErrorAction SilentlyContinue).Count }
  Write-Output "archived: $arch"
  if ($n -gt 10) { Write-Output "WARN $n active experiments - archive/close stale ones" }
}

switch ($Cmd) {
  'init' { Cmd-Init }
  'close' { Cmd-Close }
  'list' { Cmd-List }
  default {
    Write-Output 'usage: experiment.ps1 init <slug> [title] [mode] [base]'
    Write-Output '       experiment.ps1 close <slug> keep|discard [paths]'
    Write-Output '       experiment.ps1 list [write]'
    exit 2
  }
}
