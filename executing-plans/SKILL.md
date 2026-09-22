---
name: executing-plans
description: >-
  Executing Plans: execute a written implementation plan — load the plan, review it
  critically, execute all tasks in order running the verifications each task specifies,
  and report when complete. Use when you have a written implementation plan to execute in
  a separate session, or when resuming a plan in a fresh session after an agent/tool
  switch (if your agent environment can run plans with subagents, prefer that — this
  skill executes solo). NOT for: verify-only stage completion checks against a spec —
  those only verify and never execute.
slug: executing-plans
version: 1.0.2
displayName: executing-plans
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that this workflow works much better with access to subagents (Claude Code, Codex CLI, Codex App, Copilot CLI, and Gemini CLI all qualify). If your agent environment can run plans with subagents, prefer that route over this skill — this skill executes solo.

## The Process

### Step 1: Load and Review Plan
1. Ensure an isolated workspace: if your environment provides a git worktree skill or workflow, use it to create one or verify the existing one; otherwise create or verify an isolated worktree/branch yourself — never assume such a helper is installed
2. Read the plan file; if the session hasn't identified one, ask your human partner for its path — don't assume a location
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create todos for the plan items and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm finishing the development branch to complete this work."
- If your environment happens to include a branch-finishing skill, prefer following it; otherwise complete the work directly: verify the full test suite passes, present the integration options to your human partner (merge, open a PR, keep the branch, or discard), and execute their choice

## 边界（与 stage-gate 分工）

- **executing-plans**（本技能）：执行计划——逐任务实现 + 提交 + 验证。
- **stage-gate**：阶段完成检查——读 stage-spec DoD 逐条验证（只验不修，交回开发）。
- 顺序：执行完所有任务 → 阶段声称完成时 → 跑 `stage-gate` 验证阶段契约；执行过程中不做门禁，门禁结果不自己修（差异交回开发）。

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent
