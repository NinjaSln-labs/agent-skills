---
name: experiment-handoff
description: >-
  Experiment handoff for mid-project experiments and spikes. Isolates a trial in a git worktree
  (default), an in-place branch, or a project copy; records a small experiment doc
  (.experiments/<slug>.md plus a generated index); supports handing off to another agent/session;
  and on close merges the validated change back into the project (full or partial) or discards it,
  then cleans up the sandbox. Auto-detects VCS and the isolation strategy, records the base revision,
  and reuses the handoff-lint env fingerprint. This skill is mounted but USER-INVOKED ONLY: the
  agent must NOT auto-invoke it — the user runs it explicitly as /experiment-handoff. Use when the
  user explicitly invokes /experiment-handoff to start, hand off, or close an experiment/spike. NOT
  for: full-project handoff — use project-handoff; reading a full handoff — use project-intake.
slug: experiment-handoff
version: 1.0.2
displayName: experiment-handoff
disable-model-invocation: true
---

# 实验性交接（Experiment Handoff）

## 角色

你是**实验性交接**的执行者。项目进行到中途要试功能/跑测试时：**隔离出一个沙箱**（worktree/branch/copy），写一份小实验文档交接给下一个 agent/session，实验有结论后**把验证过的改动合并回主项目或丢弃**，并清理沙箱。

与 `project-handoff`（全项目状态交接）并列：本技能只管**单个实验**的隔离与回收。

## 何时使用（**已挂载 · 仅用户手动 `/experiment-handoff`**）

本技能**已挂载**（`~/.agents/skills/experiment-handoff`，用户可用 `/experiment-handoff` 调用），但 **agent 不得自主触发**——只有用户显式调用时才执行：

- **触发方式**：用户键入 `/experiment-handoff`（或明确点名该技能）；**仅手动**。
- 三段手动：① 用户 `/invoke` 本技能 ② 用户手动把会话交给另一个 agent ③ 用户手动宣告实验结束。
- **其余全自动**：探测 VCS、选隔离策略、建隔离、写文档/索引、记基线、算指纹、合并回主、清理。

## 硬约束

1. **隔离优先**——实验改动**不得污染主工作树**；一律先进沙箱。
2. **结论驱动合并**——先写 `结论/反馈`，再决定合并范围（全量/部分/丢弃）；不得先合并后补结论。
3. **可回滚**——合并前记基线（commit/快照 hash）；合并后跑验证，不通过即回滚。
4. **必清理**——收束必删沙箱（worktree/branch/copy）与临时分支；不留残留。
5. **防膨胀**——实验文档小（≤~600 tokens）；收束即迁 `archive/`；活跃实验 ≤10 条（超出先归档）。
6. **脱敏**——文档不含 API Key/密码/PII。

## 隔离策略（agent 自动选）

| 项目状态 | 策略 | 落地 |
|---|---|---|
| git 仓、`git worktree` 可用、主树干净 | **worktree（默认）** | **兄弟目录** `../<proj>-exp-<slug>` + 分支 `exp/<slug>`（不嵌在主树内）|
| git 仓、主树有未提交改动 | 先 commit/stash → worktree | worktree **看不到**未提交改动 |
| git 仓、小改动就地 | **branch**（`--mode branch`）| 直接切 `exp/<slug>` |
| 无 git / 无 commit（unborn HEAD）| **copy** | 复制到 `../<proj>-exp-<slug>`，排除 `node_modules/dist/.venv/target/.next/.git`；记快照 hash |
| 沙箱在外置盘/可能卸载 | `git worktree lock` | 防误 prune |

worktree **各自独立依赖**（无 `node_modules`）——建后需 install（pnpm 共享 store 可省）。

## 交接文档

- 位置：`<项目>/.experiments/<slug>.md`（本地私有，自动加 `.gitignore`）；索引 `.experiments/EXPERIMENTS.md`（**自动生成**，勿手改）。
- 字段（按 spike 模板：Goal→Method→Evidence→Conclusions→Next Steps）：

```markdown
- 状态: open | running | concluded | promoted | discarded
- 日期 / 标题
- Goal: 一句话问题/假设
- Method: 方法
- 隔离: <worktree|branch|copy> · 位置: <path> · 分支: <exp/slug 或 ->
- 基线: <commit 短 hash 或 copy 快照 hash>
- 环境指纹: 复用 .handoff/fp.sha（清单 .handoff/fp.txt）
- Run: 命令
- 结论: <反馈——合并依据>
- Next Steps:
- 合并计划: 全量 | 部分(<paths>) | 丢弃
- 合并结果: <merge commit / patch 文件 / 未合并>
- 清理: <命令>
## Evidence（追加式：测试/指标/观察）
```

## 工作流

```
【手动触发 1】开
- [ ] 1. 探测：git 仓？worktree 可用？主树干净？（无 git → copy）
- [ ] 2. 选隔离策略（见上表），建沙箱（worktree/branch/copy）
- [ ] 3. 写 .experiments/<slug>.md（基线 + 指纹）+ 生成索引
- [ ] 4. （worktree）cd 沙箱 && install 依赖

【手动触发 2】续 / 交办
- [ ] 5. 读文档 → `handoff-lint.sh fp check` 判环境是否变（一致→跳过复验；不一致→只复验变化维度）
- [ ] 6. 进沙箱继续实验，Evidence 追加

【手动触发 3】收
- [ ] 7. 填 结论/反馈 → 定合并计划（全量/部分/丢弃）
- [ ] 8. 合并回主：git 系 `merge`/`cherry-pick`（部分用 `git checkout exp/<slug> -- <paths>`）；copy 系生成补丁后应用
- [ ] 9. 合并后：跑测试 + `fp check` → 主项目 HANDOFF §2 留一行引用（不复制）
- [ ] 10. 清理沙箱 + 归档文档（状态 promoted/discarded）
```

## 合并回主项目（反馈驱动）

| 隔离方式 | 合并手段 |
|---|---|
| worktree / branch | `git merge --no-ff exp/<slug>`（或 `cherry-pick`）；部分合并：`git checkout exp/<slug> -- <paths>` |
| copy（非 git）| 生成补丁（脚本用 `diff -ruN` 或 `git diff --no-index`）→ 审阅后 `git apply -p1` / `patch -p1` |

- **粒度**：全量 / 部分（只带验证过的文件）/ 丢弃——由 `结论` 决定。
- **回滚**：合并前基线的 hash 是回滚锚点（`git reset --hard <base>` / `git revert`）；copy 系原副本仍在，可重来。
- **落痕**：成功后主项目 `project-handoff` §2 快照留一行 **引用**（commit/补丁路径），不复制内容。

## 防膨胀

- 收束即 `mv` 到 `.experiments/archive/`；索引自动区分 active/archived。
- 活跃实验 >10 → `list` 告警，先归档/收束旧的。
- 文档保持小；大段证据进项目 docs（引用即可）。

## 附带脚本

| 脚本 | 平台 | 说明 |
|------|------|------|
| `scripts/experiment.sh` | Linux / macOS / WSL / Git Bash | `init`（建隔离+文档）/ `close`（合并+清理+归档）/ `list` |
| `scripts/experiment.ps1` | Windows PowerShell 5.1+（UTF-8 **带 BOM**）| 同行为；参数为位置式（`-File` 下 `--x` 会被当参数名）|

零 python/node 依赖（bash 用 coreutils+git+tar；PS 用内建 + git/tar）。用法：

```bash
scripts/experiment.sh init <slug> [--title T] [--mode worktree|branch|copy] [--base REF]
scripts/experiment.sh close <slug> --keep|--discard [--paths p1,p2]
scripts/experiment.sh list
```
```powershell
experiment.ps1 init  <slug> [title] [mode] [base]
experiment.ps1 close <slug> keep|discard [paths]
experiment.ps1 list  [write]
```

## 反模式

- 实验改动直接落主工作树（无隔离）→ 污染主线
- 先合并后补结论（无反馈依据）
- 合并前不记基线（无法回滚）
- 收束不清理沙箱/分支（残留膨胀）
- 实验文档写成大百科（超预算、不归档）
- agent **自主调用**本技能（应等用户 `/experiment-handoff`）

## 完成标准

- [ ] 沙箱已建且主树未被污染（worktree/branch/copy 其一）
- [ ] 由用户 `/experiment-handoff` 显式触发（非 agent 自主调用）
- [ ] `.experiments/<slug>.md` 存在（含 Goal/Method/基线/指纹/结论/合并计划/合并结果/清理）
- [ ] 索引 `.experiments/EXPERIMENTS.md` 已生成
- [ ] 收束：按结论合并或丢弃；合并后有验证 + 主项目 HANDOFF §2 引用一行
- [ ] 沙箱/分支已清理；文档已迁 `archive/`
- [ ] 无敏感信息

## 方法论来源（2026-09 调研）

- **Technical Spike 模板**（Microsoft Engineering Playbook）：Goal / Method / Evidence / Conclusions / Next Steps——本技能文档字段来源
- **Git worktree 最佳实践**（GitWorktree.org）：兄弟目录布局、`<project>-<branch-slug>` 命名、合并后 `git worktree remove` + `prune`、每 worktree 独立依赖——隔离策略来源
- **Agent handoff 模式**（Microsoft Agent Framework / AutoGen）：显式交接控制权——手动三段触发模型来源
