---
name: git-workflow
description: >-
  Git workflow skill: branching strategies, Conventional Commits, creating or reviewing
  PRs, resolving PR review comments, merging PRs (CI verification, auto-merge queues,
  post-merge cleanup), PR review threads, signed commits, merge conflicts, Git+CI/CD
  integration, git hooks (lefthook, captainhook, husky, pre-commit), debugging
  hook-install failures in git worktrees, and GitHub release creation rules. Use when
  merging stalls on failing checks or unresolved review threads, when a hook fails to
  install in a worktree, when writing commit/branch/tag conventions, or when creating
  a GitHub release. NOT for: diagnosing BLOCKED project-workflow PR states; no skill
  name implied.
slug: git-workflow
version: 1.1.1
displayName: git-workflow
---

# Git Workflow Skill

## When to Use / How to Invoke

Invoke explicitly by name when any of these is true (do not self-trigger on ordinary git chatter):

- "merge is blocked on failing checks / unresolved review threads" → load `references/pull-request-workflow.md`.
- "hook won't install / fails in a worktree" → load `references/git-hooks-setup.md`.
- writing commit / branch / tag conventions → `references/commit-conventions.md`.
- creating a GitHub release → `references/release-rules.md`.

Invocation form: `use git-workflow: <what you need, e.g. "merge PR #42 after CI passes">`. If invoked without arguments, ask which of the trigger scenarios above applies before loading references.

**NOT for (observable boundaries):**

- Not a git repository (no `.git/` where `pwd` points) → stop; this skill has nothing to act on.
- Diagnosing BLOCKED project-workflow PR states → that is a workflow-state issue, not a git operation; no skill name implied.
- No network / GitHub unreachable: all local operations (branches, commits, rebase, hooks, `verify-git-workflow.sh`) still work; defer PR/release steps and say which command failed on connectivity.
- Wrong repo (the repo you are in is not the one the user named) → verify with `git remote -v` before any write operation; abort on mismatch.

## Quick-Start Example

Precondition: you are in a feature-branch repo with a PR waiting on CI.

Invocation:

```text
use git-workflow: PR #42 is green, merge it per the merge gate
```

What happens / typical output excerpt:

```text
Loaded references/pull-request-workflow.md.
Merge gate: threads resolved ✓ · CI green ✓ · rebased onto main ✓ · signed ✓
→ git fetch origin && git rebase origin/main
→ git push --force-with-lease origin feature/TICKET-42
→ git merge --ff-only main   (or via platform merge button)
```

Local-only check (no PR needed):

```bash
./scripts/verify-git-workflow.sh /path/to/repository
```

Output excerpt: `✅ All branch names follow conventions` / `⚠️  Non-standard branch names found: ...`. Exit code 0 when the checks ran (warnings are counted and reported, not fatal); exit 1 when the path is not a git repository (`❌ Not a git repository`).

## Critical Rules (Non-Negotiable)

1. **No direct push to main** — always open a PR.
2. **No merge before all threads resolved** — see `references/pull-request-workflow.md`.
3. **No squash unless asked** — preserves atomic commits, signatures, bisection.
4. **No "tested/verified/working" without pasted command output** — else say so.
5. **No edits to installed skill/plugin cache paths** (`~/.claude/skills/`, `~/.claude/plugins/cache/`, `**/.bare/**`) — always the repo worktree, verified by `pwd`.
6. **Force-push only with `--force-with-lease`** — never plain `--force`.
7. **Commit before rebase** — `add → commit → fetch → rebase → push`. Dirty tree aborts rebase.
8. **No editorializing** — state what changed, not how good it is; no narrating expected results or self-praise. See `references/no-editorializing.md`.

See `references/pull-request-workflow.md` for merge-gate and atomic-commit patterns.

## Reference Files

Load on demand:

| Reference | Content Triggers |
|-----------|-----------------|
| `references/commit-conventions.md` | Conventional commits, DCO sign-off |
| `references/pull-request-workflow.md` | Default-branch check, PR merge, merge gate, signed rebase |
| `references/ci-cd-integration.md` | Watching CI from the CLI, git mirror repositories |
| `references/advanced-git.md` | Rebase, cherry-pick, bisect, stash, worktrees, reflog, recovery |
| `references/release-rules.md` | GitHub releases: immutable tags and tag reuse, Latest badge, pre-create checks |
| `references/git-hooks-setup.md` | Hook frameworks, detection, hooks per stage |
| `references/claude-code-hooks.md` | Claude Code `settings.json` hooks — merge gate, cache-path rejection, auto-lint |
| `references/code-quality-tools.md` | shellcheck, shfmt, git-absorb, difftastic |
| `references/merge-gate-watcher.md` | Merge-driver loop, check taxonomy, stale-SHA rerun, review-bot rounds |
| `references/spec-cleanup.md` | Keep planning artifacts off the base branch; guard + capture-to-ADR |
| `references/no-editorializing.md` | Writing without self-praise or narrating the expected |

## Conventional Commits

```
<type>[scope]: <description>
```

**Types**: `feat` (MINOR), `fix` (PATCH), `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Breaking change**: Add `!` after type or `BREAKING CHANGE:` in footer.

## Branch Naming

```
feature/TICKET-123-description
fix/TICKET-456-bug-name
release/1.2.0
hotfix/1.2.1-security-patch
```

## Hook Detection

Detect hooks first:

```bash
ls lefthook.yml .lefthook.yml captainhook.json .pre-commit-config.yaml .husky/pre-commit 2>/dev/null || echo "No hooks"
```

Install: `lefthook install` | `composer install` | `npm install` | `pre-commit install`

## Critical Release Rules

1. **Immutable releases**: deleted releases block tag reuse; bump version.
2. **Multi-branch releases**: Use `--latest=false` from non-default branches.
3. **Pre-release**: Version bumped, CI green, CHANGELOG updated, `git pull` BEFORE `gh release create`.

## PR Merge Requirements

Before merging: threads resolved, CI green (incl. annotations), rebased, signed. Rebase-only + signed: `git merge --ff-only`.

## Verification

```bash
./scripts/verify-git-workflow.sh /path/to/repository
```

- Argument: repository path (default `.`). No flags.
- Exit 0: checks ran (fix reported ⚠️ warnings before opening/merging a PR).
- Exit 1: target is not a git repository — check `pwd` and the path argument.

## Failure Exits

| Symptom (observable) | Way out |
|----------------------|---------|
| `❌ Not a git repository` from the verify script (exit 1) | Wrong path or wrong directory; run `pwd` + `git remote -v`, rerun with the correct repo path |
| `fatal: not a git repository` from any git command | Same as above — never `git init` to make the error go away |
| Hook install prints nothing / `echo "No hooks"` fired (see Hook Detection) | No hook framework configured; pick one from `references/git-hooks-setup.md` first, then install |
| Push rejected (non-fast-forward) | Do **not** plain `--force`; commit local work, `git fetch`, `git rebase`, then `git push --force-with-lease` |
| Rebase aborts with dirty tree | Rule 7: `git add → git commit` (or `git stash`) first, then rebase |
| `gh release create` fails on existing tag | Releases are immutable — bump the version, never reuse the tag (see Critical Release Rules) |
| Network timeout on `git fetch` / `gh` | Finish all local steps, then retry the remote step once connectivity is back; state which step is pending |

## 中文速览（Quick Guide）

- **做什么**：覆盖分支策略、Conventional Commits、PR 创建/评审/合并、git hooks 安装排障与 GitHub 发布规则的实操指引，按触发场景加载对应 references。
- **何时用**：合并被失败检查或未解评审线程卡住、hook 在 worktree 装不上、写提交/分支/标签规范，或建 GitHub release 时。
- **核心步骤**：①`git remote -v` 确认在正确仓库 ②按触发场景选参考文件 ③本地操作（分支/提交/rebase/钩子） ④PR 合并走 CI 验证 ⑤发布遵循不可变 tag 规则。
- **国内可达性**：本地 git 操作全部离线可用；`gh`/GitHub PR/release 步骤依赖 GitHub，网络不通时先完成本地步骤并注明待远端的一步（正文 Failure Exits 已给此出口）。

## FAQ / Wrong Way → Fix

| Wrong way | Fix |
|-----------|-----|
| `git push --force` because "it's my branch" | `--force-with-lease` only; plain force can eat teammates' commits |
| Squashing by default for a "clean history" | Don't squash unless asked — it destroys atomic commits, signatures, bisectability (Rule 3) |
| Saying "tested and working" without pasting output | Paste the command output or say it's unverified (Rule 4) |
| Editing skills under `~/.claude/skills/` or `**/.bare/**` | Always edit the repo worktree; verify with `pwd` (Rule 5) |
| Self-triggering this skill for any git question | Only for the named trigger scenarios; otherwise answer inline without loading references |
| Merging with unresolved review threads because CI is green | Threads-resolved is a hard gate — resolve or get explicit waiver first (Rule 2) |

---

> **Contributing:** <https://github.com/netdelegated-research/git-workflow-skill>
