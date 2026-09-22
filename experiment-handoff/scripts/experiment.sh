#!/usr/bin/env bash
# experiment.sh - experimental-handoff isolation helper (init / close / list).
# Platforms: Linux / macOS / WSL / Git Bash. Windows-native: experiment.ps1 (same contract).
# Dependencies: coreutils + git(optional) + tar. No python/node needed.
#
# Usage:
#   experiment.sh init <slug> [--title T] [--mode worktree|branch|copy] [--base REF]
#   experiment.sh close <slug> (--keep | --discard) [--paths p1,p2]
#   experiment.sh list [--stale-days N] [--write-index]
#
# Isolation is auto-chosen: git repo -> worktree (default) or branch (--mode branch);
# otherwise -> copy of the project. Doc lives in <proj>/.experiments/<slug>.md (local, gitignored).
# Exit: 0 ok; 1 error; 2 usage.

set -u

usage() {
  cat >&2 <<'USAGE'
usage: experiment.sh <cmd> [args]
  init <slug> [--title T] [--mode worktree|branch|copy] [--base REF]
  close <slug> (--keep | --discard) [--paths p1,p2]
  list [--stale-days N] [--write-index]
USAGE
  exit 2
}
die() { echo "experiment: $*" >&2; exit 1; }
is_git() { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }
today() { date -u +%F; }

doc_mode() { grep -m1 '^- 隔离:' "$1" | sed 's/^- 隔离: *//' | awk -F' · ' '{print $1}'; }
doc_field() { grep -m1 "^- $2:" "$1" | sed "s/^- $2: *//"; }
iso_loc() { grep -m1 '^- 隔离:' "$1" | sed 's/^- 隔离: *//' | awk -F' · ' '{print $2}' | sed 's/^位置: *//'; }
iso_branch() { grep -m1 '^- 隔离:' "$1" | sed 's/^- 隔离: *//' | awk -F' · ' '{print $3}' | sed 's/^分支: *//'; }

write_index() {
  local dir=".experiments"
  local out="$dir/EXPERIMENTS.md"
  [ -d "$dir" ] || return 0
  {
    echo "# 实验索引（自动生成——勿手改）"
    echo
    echo "| slug | 状态 | 隔离 | 位置/分支 | 日期 | 文档 |"
    echo "|------|------|------|-----------|------|------|"
    for f in "$dir"/*.md; do
      [ -e "$f" ] || continue
      [ "$(basename "$f")" = "EXPERIMENTS.md" ] && continue
      local s st m l d b
      s=$(basename "$f" .md)
      st=$(doc_field "$f" 状态); m=$(doc_mode "$f"); l=$(iso_loc "$f"); b=$(iso_branch "$f"); d=$(doc_field "$f" 日期)
      printf '| %s | %s | %s | %s%s | %s | [%s.md](%s.md) |\n' "$s" "$st" "$m" "$l" "${b:+ / $b}" "$d" "$s" "$s"
    done
    if [ -d "$dir/archive" ]; then
      for f in "$dir/archive"/*.md; do
        [ -e "$f" ] || continue
        local s st d
        s=$(basename "$f" .md); st=$(doc_field "$f" 状态); d=$(doc_field "$f" 日期)
        printf '| %s | %s | — | 已归档 | %s | [archive/%s.md](archive/%s.md) |\n' "$s" "$st" "$d" "$s" "$s"
      done
    fi
  } > "$out"
}

cmd_init() {
  local slug="" title="" mode="" base=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --title) title="${2:-}"; shift 2 ;;
      --mode) mode="${2:-}"; shift 2 ;;
      --base) base="${2:-}"; shift 2 ;;
      -*) die "unknown option: $1" ;;
      *) [ -z "$slug" ] && slug="$1" || die "extra arg: $1"; shift ;;
    esac
  done
  [ -n "$slug" ] || usage
  echo "$slug" | grep -Eq '^[a-z0-9][a-z0-9-]*$' || die "slug must match [a-z0-9-] (lowercase)"

  local root proj; root="$PWD"; proj=$(basename "$PWD")
  [ -f .experiments/"$slug".md ] && die "experiment '$slug' already exists (.experiments/$slug.md)"

  if [ -z "$mode" ]; then if is_git; then mode=worktree; else mode=copy; fi; fi
  if [ "$mode" != "copy" ] && is_git && ! git rev-parse HEAD >/dev/null 2>&1; then
    mode=copy   # unborn HEAD -> no base revision, fall back to copy
  fi
  if [ "$mode" = "worktree" ] && ! git worktree list >/dev/null 2>&1; then mode=copy; fi

  local loc="" br="" baseref="" basehash=""
  case "$mode" in
    worktree)
      loc="../$proj-exp-$slug"; br="exp/$slug"
      [ -n "$base" ] || base="HEAD"
      basehash=$(git rev-parse --short "$base")
      [ -e "$loc" ] && die "path exists: $loc"
      git worktree add -b "$br" "$loc" "$base" >/dev/null || die "git worktree add failed"
      ;;
    branch)
      br="exp/$slug"
      [ -z "$(git status --porcelain)" ] || die "working tree not clean - commit/stash first (or use --mode worktree)"
      [ -n "$base" ] || base="HEAD"
      basehash=$(git rev-parse --short "$base")
      git switch -c "$br" >/dev/null || die "git switch failed"
      loc="(in place)"
      ;;
    copy)
      loc="../$proj-exp-$slug"; br="-"
      [ -e "$loc" ] && die "path exists: $loc"
      mkdir -p "$loc"
      local ex="--exclude=./node_modules --exclude=./dist --exclude=./.venv --exclude=./target --exclude=./.next --exclude=./.git --exclude=./.experiments"
      # shellcheck disable=SC2086
      tar -cf - $ex . | ( cd "$loc" && tar -xf - ) || die "copy failed"
      basehash=$(tar -cf - $ex . | sha256sum | cut -c1-12)
      ;;
    *) die "bad mode: $mode" ;;
  esac

  mkdir -p .experiments
  if is_git && [ -f .gitignore ] && ! grep -qx '.experiments/' .gitignore; then printf '.experiments/\n' >> .gitignore; fi
  cat > .experiments/"$slug".md <<EOF
# Experiment: $slug

- 状态: open
- 日期: $(today)
- 标题: ${title:-$slug}
- Goal: ${title:-<问题/假设>}
- Method: <方法>
- 隔离: $mode · 位置: $loc · 分支: $br
- 基线: $basehash
- Run: <命令>
- 结论:
- Next Steps:
- 合并计划: 全量
- 合并结果:
- 清理: $([ "$mode" = copy ] && echo "rm -rf $loc" || echo "git worktree remove $loc && git branch -d $br")

## Evidence

（追加式记录测试/指标/观察）
EOF

  write_index
  echo "experiment '$slug' opened"
  echo "  mode : $mode"
  echo "  loc  : $loc  branch: $br  base: $basehash"
  echo "  doc  : .experiments/$slug.md"
  if [ "$mode" = "worktree" ]; then echo "  next : cd $loc && install deps (worktrees have no node_modules)"; fi
  return 0
}

cmd_close() {
  local slug="" action="" paths=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --keep) action=keep; shift ;;
      --discard) action=discard; shift ;;
      --paths) paths="${2:-}"; shift 2 ;;
      -*) die "unknown option: $1" ;;
      *) [ -z "$slug" ] && slug="$1" || die "extra arg: $1"; shift ;;
    esac
  done
  [ -n "$slug" ] || usage
  [ -n "$action" ] || die "need --keep or --discard"
  local doc=".experiments/$slug.md"; [ -f "$doc" ] || die "not found: $doc"

  local mode loc br overall="none"
  mode=$(doc_mode "$doc"); loc=$(iso_loc "$doc"); br=$(iso_branch "$doc")

  if [ "$action" = "keep" ]; then
    case "$mode" in
      worktree|branch)
        is_git || die "doc says $mode but not a git repo"
        if [ -n "$paths" ]; then
          # shellcheck disable=SC2086
          git checkout "$br" -- $(echo "$paths" | tr ',' ' ') || die "path checkout failed"
          overall="partial: $paths"
        else
          git merge --no-ff "$br" -m "merge experiment $slug" >/dev/null || die "merge failed (resolve conflicts then re-run --keep)"
          overall=$(git rev-parse --short HEAD)
        fi
        ;;
      copy)
        local patch=".experiments/$slug.patch"
        local proj; proj=$(basename "$PWD")
        # diff main -> sandbox, from the parent dir so -p1 strips the project prefix
        ( cd .. && diff -ruN -x node_modules -x dist -x .venv -x target -x .next -x .git -x .experiments "$proj" "$proj-exp-$slug" ) > "$patch" 2>/dev/null || true
        [ -s "$patch" ] || die "no diff produced (or empty) - inspect $loc manually"
        overall="patch: $patch (apply from project root: git apply / patch -p1)"
        echo "experiment: patch written -> $patch (review then apply)" >&2
        ;;
      *) die "unknown isolation mode in doc: $mode" ;;
    esac
  fi

  # cleanup sandbox
  case "$mode" in
    worktree)
      git worktree remove --force "$loc" 2>/dev/null || true
      git worktree prune 2>/dev/null || true
      git branch -D "$br" >/dev/null 2>&1 || true
      ;;
    branch) git switch - >/dev/null 2>&1 || true; git branch -D "$br" >/dev/null 2>&1 || true ;;
    copy) rm -rf "$loc" ;;
  esac

  local status="discarded"; [ "$action" = "keep" ] && status="promoted"
  sed -i.bak "s/^- 状态:.*/- 状态: $status/" "$doc" && rm -f "$doc.bak"
  sed -i.bak "s|^- 合并结果:.*|- 合并结果: $overall|" "$doc" && rm -f "$doc.bak"
  mkdir -p .experiments/archive
  mv "$doc" ".experiments/archive/$slug.md"
  write_index
  echo "experiment '$slug' closed: $status (merge: $overall)"
  echo "  archived: .experiments/archive/$slug.md  sandbox removed: $loc"
}

cmd_list() {
  local stale=30 write=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --stale-days) stale="${2:-30}"; shift 2 ;;
      --write-index) write=1; shift ;;
      *) die "unknown option: $1" ;;
    esac
  done
  [ -d .experiments ] || { echo "no .experiments/"; return 0; }
  [ "$write" = 1 ] && write_index
  echo "active experiments:"
  local n=0 f
  for f in .experiments/*.md; do
    [ -e "$f" ] || continue
    [ "$(basename "$f")" = "EXPERIMENTS.md" ] && continue
    n=$((n + 1))
    printf '  %-20s %-12s %s\n' "$(basename "$f" .md)" "$(doc_field "$f" 状态)" "$(doc_field "$f" 日期)"
  done
  [ "$n" = 0 ] && echo "  (none)"
  local arch=0
  [ -d .experiments/archive ] && arch=$(ls .experiments/archive/*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "archived: $arch"
  [ "$n" -gt 10 ] && echo "WARN $n active experiments - archive/close stale ones (stale-days $stale)"
  return 0
}

[ $# -ge 1 ] || usage
cmd="$1"; shift
case "$cmd" in
  init) cmd_init "$@" ;;
  close) cmd_close "$@" ;;
  list) cmd_list "$@" ;;
  -h|--help) usage ;;
  *) usage ;;
esac
