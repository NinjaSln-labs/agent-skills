#!/usr/bin/env bash
# handoff-lint - HANDOFF.md budget/structure check + environment fingerprint.
# Platforms: Linux / macOS / WSL / Git Bash. Windows-native: handoff-lint.ps1 (same contract).
# Dependencies: coreutils only (wc/awk/sed/sha256sum). No python/node needed.
#
# Usage:
#   handoff-lint.sh check [HANDOFF.md]        # token budget + structure lint
#   handoff-lint.sh fp write  [projectDir]    # compute + write <dir>/.handoff/fp.sha
#   handoff-lint.sh fp check  [projectDir]    # compare; equal => env unchanged, skip re-verify
#   (both 'write'/'check' and '--write'/'--check' are accepted)
#
# Exit: 0 = pass / unchanged; 1 = over budget / changed; 2 = usage error.

set -u

TOKEN_BUDGET=1000       # estimated-token cap for HANDOFF.md
BYTES_PER_TOKEN=3       # estimate: bytes / 3

die() { echo "handoff-lint: $*" >&2; exit 2; }

est_tokens() { echo $(( ($1 + BYTES_PER_TOKEN - 1) / BYTES_PER_TOKEN )); }

cmd_check() {
  f="${1:-HANDOFF.md}"
  [ -f "$f" ] || die "not found: $f"
  bytes=$(wc -c < "$f" | tr -d ' ')
  tokens=$(est_tokens "$bytes")
  fails=0
  warns=0
  echo "HANDOFF: $f"
  echo "  size: ${bytes} B  ->  ~${tokens} tokens (bytes/${BYTES_PER_TOKEN})  budget ${TOKEN_BUDGET}"
  if [ "$tokens" -gt "$TOKEN_BUDGET" ]; then
    echo "  FAIL over budget: ${tokens} > ${TOKEN_BUDGET}"
    fails=$((fails + 1))
  else
    echo "  OK   within budget"
  fi

  # structure: expect sections ## 1..5, no ## 6, no non-standard ##
  for n in 1 2 3 4 5; do
    if ! grep -qE "^## ${n}\." "$f"; then
      echo "  FAIL missing section: ## ${n}."
      fails=$((fails + 1))
    fi
  done
  if grep -qE '^## 6\.' "$f"; then
    echo "  WARN section ## 6 (maintenance rules) should be deleted"
    warns=$((warns + 1))
  fi
  nonstd=$(grep -nE '^## ' "$f" | grep -vE ':## [1-5]\.|:## 6\.' || true)
  if [ -n "$nonstd" ]; then
    echo "  WARN non-standard section heading(s):"
    printf '%s\n' "$nonstd" | sed 's/^/         /'
    warns=$((warns + 1))
  fi

  # section 2 must not contain a commit list (double-source with git log)
  if awk '/^## 2\./{s=1;next} /^## /{s=0} s' "$f" | grep -qE '^- `?[0-9a-f]{7}'; then
    echo "  WARN section 2 contains a commit list (redundant with git log)"
    warns=$((warns + 1))
  fi

  # section 1 must not retain prior-handoff history
  if awk '/^## 1\./{s=1;next} /^## /{s=0} s' "$f" | grep -qE '前次|上次交接|前次接手'; then
    echo "  WARN section 1 retains prior-handoff history (move to cycles.md)"
    warns=$((warns + 1))
  fi

  # archive trio must exist
  d=$(dirname "$f")
  for a in cycles done pits; do
    if [ ! -f "$d/HANDOFF-ARCHIVE/$a.md" ]; then
      echo "  WARN missing HANDOFF-ARCHIVE/$a.md"
      warns=$((warns + 1))
    fi
  done

  # long lines (>200 chars) usually mean paragraphs where one-liners belong
  longn=$(awk '{ if (length($0) > 200) c++ } END { print c + 0 }' "$f")
  if [ "$longn" -gt 0 ]; then
    echo "  WARN ${longn} line(s) longer than 200 chars"
    warns=$((warns + 1))
  fi

  echo "  result: ${fails} fail / ${warns} warn"
  [ "$fails" -eq 0 ]
}

cmd_fp() {
  mode="${1:-check}"
  mode="${mode#--}"   # accept both 'write'/'check' and '--write'/'--check'
  dir="${2:-.}"
  list="$dir/.handoff/fp.txt"
  sha="$dir/.handoff/fp.sha"
  [ -f "$list" ] || die "missing fingerprint input list: $list"

  lines=""
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    kind=${line%%:*}
    val=${line#*:}
    case "$kind" in
      cmd)
        h=$( (cd "$dir" 2>/dev/null && eval "$val") 2>/dev/null | sha256sum | cut -c1-8)
        ;;
      file)
        if [ -f "$dir/$val" ]; then
          h=$(sha256sum "$dir/$val" | cut -c1-8)
        else
          h="MISSING"
        fi
        ;;
      *)
        continue
        ;;
    esac
    lines="${lines}${line} = ${h}
"
  done < "$list"
  overall=$(printf '%s' "$lines" | sha256sum | cut -c1-12)

  if [ "$mode" = "write" ]; then
    mkdir -p "$dir/.handoff"
    {
      echo "fp ${overall}"
      echo "at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      printf '%s' "$lines"
    } > "$sha"
    echo "fingerprint written: $sha (fp ${overall})"
    return 0
  fi

  [ -f "$sha" ] || { echo "WARN no $sha (run 'fp write' first)"; return 1; }
  prev=$(head -1 "$sha" | awk '{print $2}')
  if [ "$prev" = "$overall" ]; then
    echo "OK env unchanged (fp ${overall}) - skip environment re-verification"
    return 0
  fi
  echo "CHANGED env (fp ${prev} -> ${overall}) - re-verify only changed items:"
  tail -n +3 "$sha" > "$sha.tmp.$$" 2>/dev/null || true
  printf '%s' "$lines" > "$list.tmp.$$"
  diff "$sha.tmp.$$" "$list.tmp.$$" 2>/dev/null | sed 's/^/    /' || true
  rm -f "$sha.tmp.$$" "$list.tmp.$$"
  return 1
}

case "${1:-}" in
  check)
    shift
    cmd_check "${1:-HANDOFF.md}"
    ;;
  fp)
    shift
    cmd_fp "${1:-check}" "${2:-.}"
    ;;
  *)
    echo "usage: handoff-lint.sh {check [HANDOFF.md] | fp write|check [projectDir]}" >&2
    exit 2
    ;;
esac
