# 方法论、实证与工业先例（调研记录 2026-09-17）

> 用途：`version-management` 的正文只留可执行规则；「为什么这么规定、有没有证据、业界怎么做」放这里，按需加载。
> 标记：**[规范]** = 一手规范原文；**[研究]** = 同行评议实证；**[工业]** = 大厂/大项目的公开做法（非标准，但是强证据）。

---

## 一、四份规范（技能正文的骨架来源）

| 规范 | 版本 | 给出什么 | 关键条文 |
|---|---|---|---|
| Semantic Versioning | 2.0.0 | 版本位与兼容性的对应 | 已发布版本内容**不可修改**（第 3 条）；**弃用必须发 MINOR**（第 7 条）；移除必须换 MAJOR；预发布优先级低于同号正式版；**构建元数据不参与优先级比较** |
| Keep a Changelog | 1.1.0 | 人读的变更记录 | 六个分组 `Added/Changed/Deprecated/Removed/Fixed/Security`；顶部 `Unreleased`；每版本必有一条；**必须列出弃用/移除/破坏性**；用 ISO 日期；`[YANKED]` 标记损坏版本；区分「commit 流水」与「变更记录」 |
| Conventional Commits | 1.0.0 | 提交语义 → 版本位的映射 | `fix`→PATCH、`feat`→MINOR、`BREAKING CHANGE:` 或 `!` →MAJOR；其余类型对版本**无隐式影响**；约定「不要把一个提交掰成多个类型」 |
| Calendar Versioning | CalVer | 何时该用日期而不是语义 | 依发布日历而非任意数字；`YYYY.0M.MICRO` 等；适合**范围大/常变/时间敏感/外部事件驱动**；不推荐四段数字 |

补充规范：

- **PEP 440 [规范]**：Python 公开版本 `[N!]N(.N)*[{a|b|rc}N][.postN][.devN]`，local 段 `+`；排序 `.dev < a < b < rc < 正式 < .post`；`~=` 兼容发布；**epoch**（`1!`）用于换体系不倒退；SemVer 的 `-`/`+` **不得**进公开版本位（需翻译）；库不建议 `==` 精确锁。
- **Go Module version numbering [规范]**：主版本 v2+ **必须**体现在模块路径（`/v2`）；伪版本 `v0.0.0-<时间戳>-<提交前缀>`（工具生成，勿手写）；`+incompatible` 是历史标记。

## 二、实证研究：SemVer 在现实中大面积被违背

| 研究 | 数据 | 结论 |
|---|---|---|
| Raemaekers, van Deursen, Visser. *Semantic Versioning versus Breaking Changes: A Study of the Maven Repository*, **SCAM 2014** [研究] | Maven Central **7 年**发布历史，用字节码分析实际不兼容性 | 约 **1/3** 的发布**至少含一处破坏性变更**；版本号与实际兼容性显著脱节 |
| 同组扩展版（*Semantic versioning and impact of breaking changes in the Maven repository*, JSS 2016）[研究] | 上文的修订 + 破坏性变更的**实际影响**评估 | 把「违背」推进到「对下游造成多大伤害」 |
| Ochoa 等复制研究（较新 Maven 快照）[研究] | 复现上述方法 | SemVer **违背率升至 22.8%** |
| Decan, Mens, Constantinou. *What Do Package Dependencies Tell Us About Semantic Versioning?*, **IEEE TSE 2019** [研究] | **140 万+ 发布 / 12 万包 / 800 万条依赖**；引入「技术滞后（technical lag）」 | 依赖约束的选择与升级策略显著影响滞后；版本号承诺与实际升级风险并不同步 |

**对技能的直接影响**：

1. 不能把「版本位」当作兼容性保证来消费——升级要验证，尤其 0.x。
2. 作为发布者，光靠版本号不足以保护用户；**弃用 + 告警 + 迁移路径**必须一起给。
3. 「破坏性判定」值得投入自动化检测（API diff / 契约测试），因为人工判断的违背率就是上面这些数字的来源。

## 三、兼容性教义：契约之外还有隐式接口

- **Hyrum's Law** [工业/观察]：「用户足够多时，你在契约里承诺什么并不重要——系统的**所有可观察行为**都会被人依赖。」推论：性能特征、时序、错误文本、排序稳定性都会变成事实接口，所谓 **bug-for-bug 兼容**。因此破坏性判定必须覆盖「可观察行为」，不能只看文档化 API。
- **「We do not break userspace」（Linux 内核）** [工业]：一旦改动破坏既有用户态程序，**默认是内核 bug**，要修回去。这是「兼容性优先」最激进的公开承诺样本：把破坏用户当作自己的缺陷，而不是用户的迁移义务。
- 两者合起来的工程态度：**破坏是可以做的，但必须是有意识的、有窗口的、有迁移路径的决定**，而不是顺手为之。

## 四、废弃政策的工业先例

**Kubernetes Deprecation Policy** [工业] ——目前公开文档里最细的一份：

- API 版本分三轨：`v1alpha1`（实验，**可随时移除**）／`v1beta1`（预发布，引入后 ≤9 个月或 3 个次版本进入弃用，弃用后同样 ≥9 个月或 3 个次版本停止服务）／`v1`（GA，**当前主版本内不移除**，可标记弃用）。
- 元素只能**通过提升 API 版本**来移除；同一版本内不得删除或显著改变行为。
- 不得**朝着更不稳定的版本**做弃用（GA 不能弃用给 beta）。
- 已持久化的 API 版本必须始终能被解码/转换。
- 弃用要**可被机器发现**：响应头 `Warning`、审计注解、Prometheus 指标（含 `removed_release` 标签）。

**HTTP 层的标准信号** [规范]：

- `Deprecation`（**RFC 9745**，2025）：结构化字段，给出弃用生效时间，可配合 `deprecation` Link 关系指向说明。
- `Sunset`（**RFC 8594**，2019）：给出资源**关停**时间，并强调作用域受策略约束，防止被滥用。

**技能采用的折算**：把 K8s 的「分级 + 最短窗口 + 不得朝更不稳定版本弃用 + 弃用要可发现」抽象成通用规则；HTTP 场景直接点名两个 RFC。

## 五、不可变性与撤回：各注册表的能力差异

[工业] 各生态的撤回能力**极不均衡**，这决定「发布前自检」的强度：

| 注册表 | 能力 | 后果 |
|---|---|---|
| **Maven Central** | **几乎完全不可撤回**（不删不改已发布构件） | 发布前自检等级最高；错了只能发新版本 |
| **PyPI** | `yank`（PEP 592）：**标记**而非删除，安装器默认跳过 | 历史可追溯，但版本号已被占用 |
| **npm** | 72 小时内可 unpublish；`deprecate` 为标记 | 早期曾因左垫（left-pad）事件收紧策略 |
| **Go** | 模块**不可变** + 校验和数据库；`retract` 指令声明撤回 | 内容寻址式的强不可变 |
| **NuGet** | unlist（不再列出但仍可按精确版本还原） | 弱撤回 |
| **OCI 镜像** | tag 可变、digest 不可变 | 生产按 digest 固定才算可复现 |

**共性结论**：**没有哪个生态能真正「删掉」一个发布**；能做的只是标记。所以 `已发布不可改` 是纪律，不是选项。

## 六、多包/多构件策略（monorepo）

changesets 给出的三分类已成为事实术语 [工业]：

- **independent**：各包独立定号。
- **fixed**：整组**同版本号**，一起 bump 一起发——**即使某些包没有变更**。
- **linked**：整组共享版本号，但**只 bump 有变更的**（且组内 bump 取组内最高版本与最高变更级别）。

自动化工具谱系 [工业]：

- 提交驱动：`semantic-release`（单包为主）、`release-please`（manifest 记录各包当前版本，支持多 target）、`changesets`（多包优先）。
- SCM 派生：`setuptools_scm`、`hatch-vcs`、`python-semantic-release`（monorepo 模式按包各自配置）、`git describe`。
- 共性：工具**派生并写回单一源**；引入工具后任何手写的第二处版本立刻成为冲突源。

## 七、API 版本化 vs 制品版本化

- **Stripe** [工业]：日期版本 `YYYY-MM-DD`（含代号如 `2026-08-26.dahlia`）；账号**创建时钉住**版本；**每月发布向后兼容**，沿用上次主版名；升级是显式动作。
- **Kubernetes** [工业]：API group 独立版本化，`alpha/beta/GA` 三轨，见第四节。

结论：**对外契约的号**与**制品的号**可以是两条平行线；把两者合并成一个号，会在需要独立演进时立刻打架。

## 八、移动端与容器：另外两种「版本」

- **Android** [规范]：`versionCode`（正整数，单调，商店比较依据）／`versionName`（用户可见字符串）。参考：developer.android.com《Version your app》。
- **Apple** [规范]：`CFBundleVersion`（构建号，每次上传必须递增）／`CFBundleShortVersionString`（用户可见版本号）。
- **容器镜像** [工业]：tag 是**可变指针**、digest 是**内容地址**；按 digest 固定是可复现与供应链安全的基线，`:latest` 不是版本。

共同点：**内部序号**与**对外版本**分离是常态；混用会同时破坏可追溯性和用户沟通。

## 九、本技能据此做的取舍

| 取舍 | 依据 |
|---|---|
| 保留 SemVer 决策表，但补「弃用必须 MINOR」 | SemVer 2.0.0 第 7 条 |
| 兼容性判定加入「隐式接口」层与自检清单 | Hyrum's Law + 实证违背率 |
| 强制「先弃用后移除」+ 分级窗口 | K8s 政策折算 + SemVer 第 7 条 |
| 明确「已发布不可改，撤回靠 yank/deprecate」 | 各注册表能力差异（第五节） |
| CalVer 单列一节并给 epoch 逃生口 | CalVer 官方 + PEP 440 epoch |
| 多包策略采用 independent/fixed/linked 术语 | changesets 已成事实标准 |
| 不内置某生态的完整规范，只给对照表 | 渐进披露 + 避免与上游规范形成双源；细节指向 `references/ecosystems.md` |
| 不把具体版本号写进技能正文 | 单源原则：版本号永远在项目自己的版本源里 |

---

## 出处

**规范原文**

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Calendar Versioning (CalVer)](https://calver.org/)
- [PEP 440 — Version Identification and Dependency Specification](https://peps.python.org/pep-0440/)
- [PyPA — Version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/)
- [Go — Module version numbering](https://go.dev/doc/modules/version-numbers)
- [Go Modules Reference](https://go.dev/ref/mod)
- [RFC 9745 — The Deprecation HTTP Response Header Field](https://www.rfc-editor.org/rfc/rfc9745.html)
- [RFC 8594 — The Sunset HTTP Header Field](https://www.rfc-editor.org/info/rfc8594/)
- [Android — Version your app](https://developer.android.com/studio/publish/versioning)
- [.NET — Assembly versioning](https://learn.microsoft.com/en-us/dotnet/standard/assembly/versioning)

**实证研究**

- [Raemaekers et al., SCAM 2014 — Semantic Versioning versus Breaking Changes](https://ieeexplore.ieee.org/document/6975655)（[TU Delft 报告全文](https://repository.tudelft.nl/record/uuid:57a68419-8c92-445f-9c23-0fb36ece0cde)）
- [扩展版 — Semantic versioning and impact of breaking changes in the Maven repository (JSS)](https://www.sciencedirect.com/science/article/abs/pii/S0164121216300243)
- [Decan, Mens, Constantinou — What Do Package Dependencies Tell Us About Semantic Versioning? (IEEE TSE)](https://decan.lexpage.net/files/TSE-2019.pdf)

**工业先例**

- [Kubernetes Deprecation Policy](https://kubernetes.io/docs/reference/deprecation-policy/)
- [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
- [Hyrum's Law](https://www.hyrumslaw.com/)
- [Linux: WE DO NOT BREAK USERSPACE](https://linuxreviews.org/WE_DO_NOT_BREAK_USERSPACE)
- [Maven Central — Immutability](https://central.sonatype.org/publish/requirements/immutability/)
- [PyPI — Yanking (PEP 592)](https://docs.pypi.org/project-management/yanking/)
- [changesets — Linked Packages](https://changesets.dev/guide/linked-packages) · [Fixed Packages](https://changesets.dev/guide/fixed-packages)
- [Stripe — API versioning](https://docs.stripe.com/api/versioning) · [API upgrades](https://docs.stripe.com/upgrades)
- [Docker — Image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)
- [release-please monorepo example](https://github.com/amarjanica/release-please-monorepo-example) · [python-semantic-release monorepos](https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration-guides/monorepos.html)
