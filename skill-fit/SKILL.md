---
name: skill-fit
description: >-
  Skill fit: a read-only audit that matches a project against the skill catalog. Profiles the project
  (language/framework, git, tests, CI, product stage, current mounts), then reports three lists —
  skills to mount, mounted skills to unmount, and capability gaps — each with a reason and whether
  its environment prerequisites are met. Reads catalog.yaml as the single source of truth (falling
  back to installed skills' frontmatter when it is absent) and checks
  SkillHub / skills.sh only for install availability (never stored). Writes a local feedback record
  and can file a privacy-stripped report as a GitHub issue on NinjaSln-labs/agent-skills so
  recommendations improve over time. This skill is mounted but
  USER-INVOKED ONLY: the agent must NOT auto-invoke it — the user runs it explicitly as
  /skill:skill-fit. Use when the user explicitly invokes /skill:skill-fit to audit or fit skills for
  a project. NOT for: creating/editing a skill (use skill-builder / skill-description-audit).
slug: skill-fit
version: 1.2.0
displayName: skill-fit
disable-model-invocation: true
---

# 技能适配管家（Skill Fit）

## 角色

你是**技能适配管家**。给定一个项目，产出「**该挂什么 / 该摘什么 / 缺什么**」三张清单——**只读第一版：只建议，不擅自动手**。

单一数据源：真源仓 `catalog.yaml`（每技能的 `tier` / `when` / `requires` / `invoke` / `status`）。registry 占用状态**不落表**，用 `scripts/skill-name-check` 实时查。

## 何时使用（**已挂载 · 仅用户 `/skill:skill-fit`**）

本技能已挂载，但 **agent 不得自主触发**（frontmatter `disable-model-invocation: true`）——只有用户显式调用时才执行：
- 用户键入 `/skill:skill-fit`（可带项目路径参数，默认当前目录）
- 用途：给某项目做技能体检——**建议挂载 / 建议摘除 / 能力缺口**；对已发布用户，收集其反馈
- **其余全自动**：画像探测、对照 catalog、生成三清单、写反馈记录

## 硬约束

1. **只读 v1**——**不改**任何技能、不增删符号链接、不改项目文件；只输出建议（执行安装/摘除由用户确认后再做，或下版本的可执行模式）。
2. **单源**——推荐依据只来自 `catalog.yaml`；不在本技能正文复制 tier 清单（防双源）。
3. **registry 状态实时查**——SkillHub/skills.sh 占用用 `scripts/skill-name-check`；不写进 catalog。
4. **`requires` 先判**——环境不满足的前置（如无 git）→ 该技能降级/剔除，并说明原因。
5. **反馈不撒谎**——记录用户对建议的**采纳/否决**，不美化。
6. **外部反馈脱敏**——投递 GitHub Issue **前**先展示报告给用户确认；报告不含本机路径/仓库名/凭据/代码内容。
7. **不自带副本**——**禁止**把 `catalog.yaml` 复制进本技能（`references/` 等）；副本必然漂移。缺 catalog 时按 frontmatter 推断并**声明降级**。

## 数据源定位（通用发行版 · 自包含）

本技能**不假设自己位于真源仓**（安装方式可能是 skills.sh 整仓 / 单技能拷贝 / 项目级链接）。按下列顺序定位：

1. **catalog 定位**（取第一个存在的）：
   - `<本技能目录>/../catalog.yaml`（整仓安装——常态）
   - `<项目根>/catalog.yaml`（项目自带适配目录）
   - `<项目根>/.agents/skills/catalog.yaml`（项目级挂载）
2. **都没有 → 降级为「按 frontmatter 推断」**：扫已装技能的 `SKILL.md` frontmatter（`description` 的场景线索当 `when`，`compatibility` 当 `requires`），**显式声明**「无 catalog，本次依据为推断」，并建议用户补一份 catalog。
3. **registry 查重**：优先 `<本技能目录>/../scripts/skill-name-check.{sh,ps1}`；缺失 → 直接调端点（SkillHub `GET https://api.skillhub.cn/api/v1/skills/{slug}?namespace=<handle>`；skills.sh `GET https://skills.sh/api/search?q=<name>`）；网络不可用 → 标注「占用未核验」，**不臆断**。

## 项目画像探测（只读）

| 信号 | 探测方式（只读） |
|------|------------------|
| 语言/框架 | `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `*.csproj`；依赖里的 react/electron… |
| 版本控制 | 有 `.git`？工作树是否干净？有无 `HANDOFF-ARCHIVE/` |
| 测试/CI | `test*/` `*_test.*` `*.spec.*`；`.github/workflows/` `.gitlab-ci.yml` |
| 产品阶段 | `docs/`（PRD/定位/调研）、`HANDOFF.md`、`.experiments/`、`docs/decisions/` |
| 已有挂载 | 用户级 `~/.agents/skills/`（含符号链接指向）；项目级 `<proj>/.agents/skills/` |
| 领域 | DDD 痕迹（`UBIQUITOUS_LANGUAGE.md`、`docs/domain`）、前端（`src/components`）、营销（`docs/marketing`） |

## 对照 catalog 出三清单

1. **建议挂（mount）**：`when` 命中画像 且 `requires` 满足 且当前未挂 → 给**挂载方式**（用户级/项目级）与理由。
2. **建议摘（unmount）**：当前已挂但 `when` 不命中 或 `requires` 不满足 或 `tier=project` 却挂在用户级常驻位 → 建议摘除（并指出去哪找安装源）。
3. **缺口（gap）**：画像显示需要但 catalog 里**没有**对应技能的能力（例：系统/环境维护类当前缺）→ 明说「暂无技能，可后补」。

对每条给出：技能名 · 理由（命中的 `when` 标签）· `requires` 满足情况 · 安装坐标（本地真源链入 / skills.sh `npx skills add NinjaSln-labs/agent-skills` / SkillHub）。

## 输出格式

```
## Skill Fit — <项目名>
画像：语言=… · git=… · 测试=… · CI=… · 阶段=… · 已挂=N（用户级 a / 项目级 b）

### 建议挂（N）
- <skill> — 命中 when=[…]；requires 满足；怎么挂：<命令>

### 建议摘（N）
- <skill> — when 不命中 / requires 缺 <x>；原安装源：<…>

### 缺口（N）
- <能力> — catalog 无对应技能（可后补）

### 反馈
本次建议你采纳了哪些？否决了哪些为什么？（写入下方反馈文件）
```

## 反馈闭环（持续改进）

- **本地记录**（默认）：写 `.skill-fit/feedback/<YYYY-MM-DD>-<project>.md`，含：画像信号 + 三清单 + **用户采纳/否决**。下次运行读历史，避免重复建议、校准 `when`/`requires`。
- **外部用户反馈渠道 = GitHub Issue**（公开仓 `NinjaSln-labs/agent-skills`）：`--share` 时生成脱敏报告并按序投递——
  1. 有 `gh`：`gh issue create --repo NinjaSln-labs/agent-skills --title "[skill-fit] <项目类型> · 反馈" --body-file <报告路径> --label enhancement`
  2. 无 `gh`：打印预填 URL `https://github.com/NinjaSln-labs/agent-skills/issues/new?title=<编码标题>&body=<编码正文>`，由用户手动提交
  - **脱敏口径**：仅含「项目类型画像（语言/框架 · 是否 git · 是否有测试 · 阶段）+ 三清单 + 裁决 + 本技能版本」；**不含**本机路径、仓库名、凭据、代码内容。**提交前必须展示给用户确认**。
- 稳定后（v2）再上「生成 + 可执行安装」（挂载/摘除/选装命令一键执行）。

## 反模式

- agent **自主调用**本技能（应等用户 `/skill:skill-fit`）
- 未经确认就增删挂载（v1 只读）
- 推荐依据脱离 `catalog.yaml` 自造清单（双源）
- 把 registry 占用状态写进 catalog（应实时查）
- 忽略 `requires`（给没装 git 的环境推 git-workflow）
- 反馈记录美化/漏记否决
- 未经用户确认就把反馈提交成 GitHub Issue（或报告未脱敏）
- 把 `catalog.yaml` 复制进技能目录当默认值（双源漂移）
- 缺 catalog 时**不声明**降级、把推断结果当成单源事实

## 完成标准

- [ ] 由用户 `/skill:skill-fit` 显式触发（非 agent 自主）
- [ ] 画像信号已探测（语言/框架 · VCS · 测试/CI · 阶段 · 当前挂载）
- [ ] 三清单产出（建议挂 / 建议摘 / 缺口），每条含理由 + `requires` 判定 + 安装坐标
- [ ] **未**修改任何技能或挂载（只读）
- [ ] 反馈记录已写（含采纳/否决）；`--share` 报告经用户确认后以 GitHub Issue 投递（脱敏，无本机路径/凭据）
- [ ] 数据源已按「定位顺序」解析；catalog 缺失时已**显式声明**为 frontmatter 推断降级

## 方法论来源（2026-09 调研）

- Agent Skills 规范可选字段：`compatibility`（环境前置）、`metadata`、`disable-model-invocation`（仅用户调用）——见 agentskills.io 规范与 Pi/Claude Code 字段表
- Progressive disclosure（metadata 常驻、正文按需）——技能适配与 token 预算的依据
- 运维口径：`catalog.yaml` 单源 + registry 实时查（防双源）
