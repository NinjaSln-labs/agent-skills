---
name: version-management
description: >-
  Universal version management for any software artifact, independent of any VCS. Decides the next
  version from the change set under Semantic Versioning (MAJOR/MINOR/PATCH, prerelease, build
  metadata), keeps exactly one version source, maintains a Keep-a-Changelog CHANGELOG, and marks
  releases — VCS tags when git is available, otherwise a RELEASES manifest. Judges breaking versus
  compatible changes against the public contract (including implicit interfaces), applies
  deprecate-then-remove policies, handles immutable releases (yank/deprecate, never re-release),
  audits version consistency across files, and aligns multi-artifact releases. Use when choosing or
  bumping a version number, writing a CHANGELOG or release notes, marking a release, planning a
  deprecation, or checking that version numbers agree across a project — including projects without
  version control.
  NOT for: git branching / commit / PR flow, or dependency pinning and vulnerability
  scanning.
slug: version-management
version: 1.2.1
displayName: version-management
---

# 版本管理（Version Management）

## 角色

跨语言、跨 VCS 的版本管理：**定号 → 记变更 → 标发布 → 查一致**。没有 git 也能完整执行（退化为文件约定）。

核心判断只有一句：**版本号是对使用者的兼容性承诺**，不是构建次数计数器。

## 触发场景

- 该发哪个版本号？这次改动算 MAJOR / MINOR / PATCH？
- 这个改动算不算「破坏性」？边界在哪？
- 要废弃一个功能，怎么排期才不算突然袭击？
- 写或更新 CHANGELOG、发布说明
- 标记一次发布（有 git → tag；无 git → RELEASES 清单）
- 审计多处版本号是否一致、多构件/多包发布是否对齐

## 硬约束

1. **单版本源**——一个制品只认**一处**版本号（`SKILL.md` frontmatter / `VERSION` / `package.json` 字段 / 语言惯例…）；其余全部派生。发现两处独立维护 → **先归一，再 bump**。
2. **已发布不可改**——版本号一旦发布即冻结内容；纠错走**新版本号**。撤回用生态的 yank/deprecate 机制，**绝不重发同号**。
3. **不猜兼容性**——破坏性判定以**对外契约**为准，且必须考虑**隐式接口**（见下）。无法判定时问用户，不默认。
4. **不越界**——只管版本号；分支/提交/PR 走 `git-workflow`，依赖版本与漏洞走 `dependency-scan`。
5. **决策可回溯**——版本决策的依据（破坏了什么契约、为什么是这一位）要能查得到，不只在脑子里。

## 定号：SemVer 决策表

| 变更性质 | 版本位 | 例 |
|---|---|---|
| 破坏对外契约（不兼容） | **MAJOR** | 删除/改名公开 API、改必填参数、改数据格式、改错误语义 |
| 向后兼容地新增能力 | **MINOR** | 新增可选 API/字段/子命令 |
| **标记弃用**（功能仍在） | **MINOR** | 规范硬性要求：弃用必须发 MINOR，移除只能换 MAJOR |
| 向后兼容地修正 | **PATCH** | 修 bug、改文案、内部重构 |
| 仅元数据（文档/注释/测试） | **PATCH** | 无行为变化 |
| `0.y.z`（未稳定期） | 语义放宽 | `y` 增可含破坏性，`z` 增为修正 |

**判定顺序**：是否破坏对外契约 → 是否新增能力 → 是否弃用 → 否则 PATCH。**有疑一律取更高位**（规范的态度：破坏性变更要让人付出「换大版本」的思考成本）。

细节：MAJOR 提升时 minor/patch 归零；MINOR 提升时 patch 归零；不得前导零；`0.y.z` 期间任何东西都「可以」变，但**应告知**。

## 兼容性怎么判（比「有没有文档」难的部分）

三层，从外到内：

| 层 | 内容 | 破坏它算不算 MAJOR |
|---|---|---|
| 文档化契约 | README/API 参考/类型签名明确承诺的行为 | 算 |
| **可观察行为（隐式接口）** | 时序、错误码、日志格式、排序稳定性、性能量级、边界值 | **算**（用户已经依赖了） |
| 纯实现细节 | 私有函数、内部数据结构、未承诺的性能微差 | 不算（但也可能变成上面那层） |

**Hyrum's Law**：用户足够多时，**所有可观察行为都会被某个人依赖**。所以「规则上说这不是 API」不足以豁免破坏性——要按**实际被依赖的行为**判断。

**实证警告：不要信任版本号。** 对 Maven Central 的研究发现约**三分之一**的发布含至少一处破坏性变更；后续复制研究给出 **22.8%** 的 SemVer 违背率。含义是双向的：

- 作为**发布者**：你的 MINOR/PATCH 也可能被用户当成破坏性，所以「弃用 + 告警 + 迁移路径」比版本号本身更能救人。
- 作为**使用者**：不能只看版本位就升级，尤其对 0.x 与低成熟度依赖。

**破坏性变更清单（自检用）**：删除/重命名公开符号 · 改函数签名或参数必填性 · 改返回类型/结构/字段名 · 改错误类型、错误码、异常语义 · 收紧输入校验 · 改默认值 · 改序列化格式 · 提高最低运行环境要求（语言/运行时/OS 版本） · 移除配置项或 flag · 改 CLI 输出格式（若被脚本解析） · 改排序/分页/去重行为 · 显著性能回退或资源占用变化 · 依赖的传递升级导致上述任一。

能自动检测就自动：API diff、契约测试、编译/类型检查、黄金文件对比。**不能不检测就宣布 MINOR。**

## 废弃政策（先弃用、后移除）

规范链条：**弃用 → 发 MINOR → 至少经过一个 MINOR → 下一个 MAJOR 才移除**。破坏性变更绝不能突然到来。

分级窗口（借鉴 Kubernetes 的成熟做法）：

| 稳定级别 | 弃用后最短存活 |
|---|---|
| 稳定/GA | 当前主版本内**不移除**；弃用需公告 |
| Beta | 约 3 个次版本或 9 个月（取更长） |
| Alpha | 可随时移除，无需事先公告 |

**弃用的四件套**（缺一不可）：文档标注 · 运行时告警 · 迁移路径 · 时间线（何时移除）。可直接套用的文本模板见 [`references/deprecation-templates.md`](references/deprecation-templates.md)。

HTTP / API 场景用标准信号，便于调用方**自动化**发现：`Deprecation` 响应头（RFC 9745）给生效时间 + `Sunset` 头（RFC 8594）给关停时间 + `Link` 指向迁移文档。禁止「删了再发公告」。

## 选型：SemVer 还是 CalVer

- **SemVer**：有明确对外 API、使用者依赖兼容性承诺——库、框架、CLI、SDK。
- **CalVer**：范围大或常变（OS、发行版）、时间敏感（证书、时区库）、由外部事件驱动发布（如按日期切版的 API 服务）。CalVer 直接传达「什么时候的」，且能配合支持周期做算术。
- **切换排序会断**：从 CalVer 切到 SemVer 会出现 `1.0 < 2014.04` 的倒挂 → 用 **epoch**（PEP 440 的 `1!`、Debian/RPM 的 epoch）把新体系整体抬到旧体系之上。epoch 只在一生用一次，用了就别回头。
- 四段数字不推荐（CalVer 明说）；预发布/构建元数据只在 SemVer 里有标准语义。

## 不可变发布

- **已发布 = 内容冻结**。同一版本号下的字节永不改变；再次构建产物用构建元数据/摘要标记，不改版本号语义。
- **撤回手段按生态**（都是「标记」而非「抹除历史」）：PyPI `yank`（PEP 592）、npm `deprecate`、Go `retract`、NuGet unlist；Maven Central 基本**不接受**撤回与重发。所以发布前自检，比事后撤回重要得多。
- **安全事件**：CHANGELOG 里标 `[YANKED]` 并写明原因——响亮、可被解析、可被搜寻。
- **制品不可变 ≠ 标签不可变**：容器镜像 tag 是可变指针，同一个 `:1.2.3` 可能指向不同 digest；生产环境按 **digest** 固定，tag 只作人类可读别名。`latest` 不是版本号。

## 单版本源与自动化

1. **定位唯一源**（先读，再改）：`package.json` / `pyproject.toml` / `Cargo.toml` / `*.csproj` / `VERSION` / `SKILL.md` frontmatter / 语言惯例。
2. **只改这一处**，其余派生（README 版本表、清单索引、CHANGELOG 标题）。
3. 发现同号多写 → 标注「应派生」并归一：这是漂移的**唯一**根因。
4. 改完**回查一致**。

自动化在「派生」上做，不在「新增源」上做（选**一套**，别叠）：

| 驱动方式 | 代表 | 适用 |
|---|---|---|
| 规范提交 → 自动定号 | semantic-release、release-please（manifest）、changesets | 已用 Conventional Commits 的项目 |
| 从 SCM 派生版本 | setuptools_scm、hatch-vcs、`git describe` | 以提交历史为真相、不想手写号 |
| 显式文件 + 人写 | `VERSION`、frontmatter | 无 VCS 或需人工把关 |

**共性**：工具只负责**派生与写回单一源**；一旦工具自动改写版本号，任何手写的第二处就会立刻变成冲突源。自动生成的 CHANGELOG **仍需人审**（它是给使用者看的，不是 commit 转储）。

## CHANGELOG（Keep a Changelog 约定）

- 文件 `CHANGELOG.md`，**最新在顶部**，每版本一节：`## [X.Y.Z] - YYYY-MM-DD`（ISO 日期，避免歧义）。
- 分组固定：`Added / Changed / Deprecated / Removed / Fixed / Security`（空组不写）。
- 面向**使用者**写「变了什么」，不写 commit 流水；**每个版本都要有一条**，不一致的 CHANGELOG 比没有更危险。
- `## [Unreleased]` 先攒，发布时落成版本号。
- **必须显式列出**：废弃项、移除项、任何破坏性变更（这是读者最需要的一行）。
- 损坏版本标 `## [0.0.5] - 2014-12-13 [YANKED]`。
- 无 VCS 时，CHANGELOG 就是变更的**唯一时间线**。

## 发布标记

- **有 VCS（git）**：在发布提交上打 `vX.Y.Z` tag（附注 tag 可承载发布说明）。**只标记，不重写历史**；移动已发布 tag 属于 `git-workflow` 边界且需用户确认。
- **无 VCS**：维护 `RELEASES.md`（或 `releases.json`）——每条：版本号 · 日期 · CHANGELOG 锚点 · 制品摘要（如 sha256）。
- **顺序**：先写版本源与 CHANGELOG → 再打标记；打错只删标记，不动制品。

## 预发布与构建元数据

- 预发布：`X.Y.Z-alpha.N` / `-beta.N` / `-rc.N`。同一序列数字递增；**正式发布去掉后缀**，不回改已发布的预发布号。
- 排序：`1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-beta < 1.0.0-rc.1 < 1.0.0`；数字段按数值比、字母段按 ASCII 比，数字段优先级更低。
- 构建元数据：`X.Y.Z+<build>`——**不参与优先级比较**，只作标识。
- 生态翻译：SemVer 的 `-`/`+` 在部分生态不合法（如 Python 公开版本位），需翻译（用 `.devN`/local 段），不要硬塞。

## 多构件 / 多包对齐

三种策略，**选一种并写进仓库**（术语取自 changesets）：

| 策略 | 行为 | 适用 |
|---|---|---|
| **independent** | 各自独立定号 | 各包生命周期无关 |
| **fixed** | 整组**同版本号**，有变更就整组发（含无变更的包） | 必须成对升级的套件 |
| **linked** | 整组共享号，但**只 bump 有变更的** | 同族但非强绑定 |

跨包引用用**范围**而非精确号（除非有意锁定）；同批发布在 CHANGELOG 里说明适用范围。

## 输出格式

```
## 版本决策
现状：当前 <X.Y.Z>（源：<文件:行>）· 变更：<摘要>
判定：<MAJOR/MINOR/PATCH>  · 理由：<破坏哪条契约 / 新增什么 / 是否弃用>
## 落地
- 版本源：<文件:行> → <X'.Y'.Z'>
- CHANGELOG：<新增节 + 分组条目（含废弃/移除/破坏性显式列出）>
- 发布标记：git tag `vX'.Y'.Z'` 或 RELEASES 记录
- 一致性回查：<引用点清单 → 全部一致 / 待改 …>
- 破坏性自检：<清单比对结果 / 自动检测手段与结果>
```

## 反模式

- 同一版本号多处独立维护（必然漂移）
- 破坏性变更只发 PATCH/MINOR，用版本号掩盖破坏性
- 仅文档改动就发 MAJOR（噪音）；或弃用不发 MINOR
- 无弃用窗口直接移除；删了之后再补公告
- 重发/复用/递减已发布版本号；同号改内容
- 把 tag 或镜像 tag 当版本号真相（tag 可变）
- CHANGELOG 写成 commit 罗列，或事后补写失真
- 无 VCS 时不留任何发布记录（丢失时间线）
- 越界去改 git 历史、移动已发布的 tag

## 完成标准

- [ ] 版本源定位到**唯一**一处并已更新，引用点回查一致
- [ ] bump 位次有依据（对照决策表，说明破坏/新增/弃用哪一类）
- [ ] 破坏性判定有依据或检测手段（不只是「我觉得兼容」）
- [ ] 涉及弃用时：四件套齐全（文档 · 告警 · 迁移路径 · 时间线）且窗口合规
- [ ] CHANGELOG 新增版本节 + 分组条目（废弃/移除/破坏性显式列出）
- [ ] 发布标记按环境落位（git tag 或 RELEASES 记录）
- [ ] 未触碰 VCS 历史、未改已发布版本号

## 参考资料（渐进披露）

- [`references/ecosystems.md`](references/ecosystems.md)——各生态版本格式/排序/范围/不可变性对照表（npm · Python · Go · Maven · NuGet/.NET · Android · Apple · OCI · K8s · Stripe）
- [`references/deprecation-templates.md`](references/deprecation-templates.md)——弃用公告模板集（文档标注 · 运行时告警 · `Deprecation`/`Sunset` 头 · CHANGELOG 条目 · 迁移指南骨架 · 自检清单）
- [`references/research.md`](references/research.md)——方法论来源、实证数据、工业先例与出处清单

## 方法论来源（摘要）

Semantic Versioning 2.0.0 · Keep a Changelog 1.1.0 · Conventional Commits 1.0.0 · Calendar Versioning（CalVer）· PEP 440 · Go Module version numbering · Kubernetes Deprecation Policy · Hyrum's Law · RFC 9745 / RFC 8594。完整出处见 [`references/research.md`](references/research.md)。
