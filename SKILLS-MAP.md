# 技能库全景图（89 技能——产品 0-1 全阶段模式）

- 日期：2026-08-16 · **新增 6 技能（spec-kit 阶段门禁族：stage-gate / stage-spec / decision-log / coverage-matrix / audit-item / skill-eval——需求规格 `.scratch/neonforge-v1/skill-requirements-20260816.md`）** · 2026-08-13 全量审计 81/81 合规（新技能接入后按审计流程补 DESCRIPTION-AUDIT）
- 覆盖：本仓库 `agent-skills` 的 89 个技能（可安装到 `~/.agents/skills/<name>`）
- 模式：**产品 0-1 全生命周期**（发现 → 定义 → 设计 → 交付 → 上线 → 运营）+ 贯穿层（质量/工程/协作/技能基建）

---

## 一、按阶段分类

### ① 发现（16）—— 问题 / 市场 / 用户 / 竞品

#### 1.1 用户研究（3）

| 技能 | 能力 |
|------|------|
| user-research | 用户研究（招募/访谈/证据分级）|
| delegated-research | 通用调研（广度→深度→核实——证据链）|
| discovery-interview-prep | 发现访谈准备（问题设计/防引导）|

#### 1.2 问题定义（4）

| 技能 | 能力 |
|------|------|
| problem-statement | 问题陈述（单句痛点 + 证据锚点）|
| jobs-to-be-done | JTBD 任务映射（场景→需求→验收）|
| proto-persona | 原型人物（实证锚定——防虚构画像）|
| customer-journey-map | 客户旅程地图（阶段/触点/情绪/机会）|

#### 1.3 市场竞品（7）

| 技能 | 能力 |
|------|------|
| competitive-analysis-process | 六步竞争分析（编排——景观→战略方向）|
| market-landscape-scan | 市场景观扫描（细分/玩家/动态/空白——Step1）|
| competitive-research-snapshot | 竞品快照（产品对比矩阵——Step2）|
| voice-of-customer-miner | 客户之声挖掘（评论/社区——需求满足度——Step3）|
| company-intel | 公司情报（财务/组织/渠道——Step4——11 节输出）|
| competitive-intel-watch | 竞品方向监测（TECHINT/HUMINT/FININT/MASINT 融合——Step6 节奏）|
| battle-card-builder | 战斗卡（竞争分析 Step7 产出）|

#### 1.4 调研纪律（2）

| 技能 | 能力 |
|------|------|
| autonomous-investigation | 自主调研（Fact/Inference/Assumption 证据纪律）|
| intelligence-collection-disciplines | 情报收集纪律（SIGINT/HUMINT/FININT/MASINT/TECHINT 通道）|

### ② 定义（7）—— 定位 / 需求 / 规格 / 立项

#### 2.1 定位（2）

| 技能 | 能力 |
|------|------|
| positioning-statement | 定位陈述（对谁/解决什么/为何不同）|
| positioning-workshop | 定位工作坊（多候选→收敛）|

#### 2.2 需求规格（4）

| 技能 | 能力 |
|------|------|
| prd-driven-ddd | **PRD 驱动 DDD 主入口**（场景验证→架构映射→落地链路）|
| write-spec | 规格编写（背景/范围/成功标准/接口契约）|
| prd-development | PRD 开发（上下文/目标/用户故事/验收）|
| press-release | 新闻稿式产品定义（亚马逊逆向工作法）|

#### 2.3 拆解立项（1）

| 技能 | 能力 |
|------|------|
| to-tickets | 需求拆解为 ticket（垂直切片 + AI-ready 验收标准 predicates）|

### ③ 设计（23）—— 领域 / 架构 / 规范 / 视觉

#### 3.1 领域建模 DDD（9）

| 技能 | 能力 |
|------|------|
| ddd-scope | DDD 范围收敛（问题陈述/目标/约束/术语种子/风险）|
| ddd-discover | 领域发现（事件流/命令/热点/歧义）|
| ddd-subdomains | 子域分类（Core/Supporting/Generic）|
| ddd-contexts | 限界上下文 + 通用语言 + 边界 ADR |
| ddd-context-map | 上下文映射（集成模式/契约所有权/失败模式）|
| ddd-aggregates | 聚合设计（不变量/边界/事务）|
| ddd-domain-interactions | 领域交互（事件/服务/仓储/工厂）|
| ddd-openspec-bridge | DDD → OpenSpec 桥接（结构化规范）|
| event-storming | EventStorming 工作坊（Big Picture/Process/Design-Level）|

#### 3.2 模型评审（2）

| 技能 | 能力 |
|------|------|
| ddd-model-review | 模型质量评估（一致性/完整性/耦合——回溯触发）|
| ddd-tactical-review | 战术 DDD 评审（贫血模型检测/富领域重构）|

#### 3.3 架构设计（3）

| 技能 | 能力 |
|------|------|
| architecture-patterns | Clean/Hexagonal/DDD 实现架构（依赖规则/端口适配器）|
| codebase-design | 深度模块设计（接口/接缝/可测试性——mattpocock）|
| deep-codebase-analysis | 代码库全面分析（架构/通信/模式/约定/业务流/状态/错误处理 7 维）|

#### 3.4 编码规范（3）

| 技能 | 能力 |
|------|------|
| typescript-best-practices | TS 最佳实践（类型/模式/工程规范）|
| react-vite-best-practices | React + Vite 最佳实践（组件/性能/工程）|
| electron-best-practices | Electron 最佳实践（主/渲染进程/安全/打包）|

#### 3.5 视觉设计（6）

| 技能 | 能力 |
|------|------|
| frontend-design | 前端设计（组件/页面——两遍法+自评）|
| ui-ux-pro-max | UI/UX 交互设计（设计系统/一致性）|
| web-design-guidelines | Web 设计规范（排版/色彩/可及性——WebFetch 降级）|
| ux-heuristics | 可用性启发式审计（Nielsen 10/Krug 定律/严重度评级——wondelai v1.6.0）|
| ui-typography | 专业排版规则（引号/破折号/间距/层级——ENFORCEMENT+AUDIT 双模式——Butterick）|
| ui-animation | 设计工程与动效决策（Emil Kowalski——动画框架/组件原则/隐形细节）|

### ④ 交付（20）—— 计划 / 实现 / 测试 / 质量

#### 4.1 计划执行（4）

| 技能 | 能力 |
|------|------|
| writing-plans | 实施计划编写（任务拆解/文件路径/验证步骤）|
| stage-spec | **阶段契约编写/回填**（DoD 机器可验证断言 + TDD 网格 + 边界——被 stage-gate 执行）|
| executing-plans | 计划执行（加载→批判性审查→逐任务执行→汇报）|
| roadmap-planning | 产品路线图规划（目标/里程碑/优先级）|

#### 4.2 工程协作（1）

| 技能 | 能力 |
|------|------|
| git-workflow | Git 工作流（分支策略/Conventional Commits/CI 集成——37★）|

#### 4.3 测试链（10）

| 技能 | 能力 |
|------|------|
| ddd-qa-chain | 质量链编排（L1 单测→L2 契约→L3 组件→L4 E2E→L5 视觉 + DoD 门禁——**层概念通用，工具命令按项目映射探测**；含金字塔梯度/V&V 确认层/flaky 治理）|
| coverage-matrix | **覆盖矩阵**（不变量↔测试 / 事件↔测试 / DoD↔门禁 三向表 + 缺口入审计项）|
| playwright-best-practices | Playwright 最佳实践（选择器/断言/稳定性）|
| pixel-perfect | 视觉回归（像素对比——默认免费）|
| visual-regression-tester | 视觉回归（双路线——Playwright 免费 + Chromatic/Percy 商业）|
| accessibility-auditor | 可及性审计（WCAG 2.1 AA——axe + 键盘/焦点）|
| api-contract-validator | API 契约验证（OpenAPI/JSON Schema/消费者契约）|
| k6-performance | 性能测试（k6——阈值/场景/自定义指标）|
| test-data-generation | 测试数据生成（Faker/工厂/构建器/种子）|
| cicd-pipeline | CI/CD 配置（GitHub Actions/Jenkins/GitLab CI）|

#### 4.4 质量审查（6）

| 技能 | 能力 |
|------|------|
| code-review | 代码审查（diff/PR——bug/风格/约定 + **阶段末即时评审模式**：固定点=阶段首 commit^、状态化 open/fixed/recorded 报告）|
| stage-gate | **阶段门禁执行**（读 stage-spec DoD 逐条验证——L1/L2/L3/行为验收/覆盖矩阵/审计项/push——只验不修）|
| audit-item | **审计问题 issue 化跟踪**（NNN-slug + 索引——open/fixed/recorded，被 stage-gate 枚举）|
| verification-before-completion | 完成前验证（行为保持——规范）|
| systematic-debugging | 系统化调试（假设/二分/证据——代码缺陷路径）|
| problem-handling | **问题处理单链**（诊断→严重度分级→workaround/永久修复→TDD 修复→验证→无责收尾+known-error；含 3-strikes 升级）**（合并自 problem-dive + problem-resolution-flow）**|

#### 4.5 质询（2）

| 技能 | 能力 |
|------|------|
| plan-grilling / grill-me | 计划/设计质询（用户触发——执行前压力测试）|

### ⑤ 上线（1）

| 技能 | 能力 |
|------|------|
| product-launch | 产品发布（ORB 框架 + 五阶段 + Product Hunt 策略 + 清单）|

### ⑥ 运营（2）

| 技能 | 能力 |
|------|------|
| product-marketing | 产品营销上下文（.agents/product-marketing.md 共享语境）|
| marketing-copywriting | 营销文案（价值主张/情感/转化——15 节）|

### 贯穿层（17）—— 质量 / 工程 / 协作 / 技能基建

#### P.1 技能基建 / 审计（4）

| 技能 | 能力 |
|------|------|
| skill-description-audit | 技能描述审计（description↔正文交叉验证 + 结构/语言/名称/误触发防护 + **pushy 质量（场景/关键词密度）**——自审只出报告）|
| skill-eval | **skill 行为评估**（3-5 代表任务 × 有/无 skill N≥3 次 → pass-rate 对比表 + 失败案例反哺）|
| skill-fit | **技能适配管家**（按项目画像对照 `catalog.yaml` 出「建议挂/建议摘/缺口」三清单；只读 v1；**仅用户 `/skill:skill-fit`**）|
| product-doc-audit | 产品文档集审计（三层 + 就绪度评分 + 四层 go/no-go 最终验收）|

#### P.2 安全（4）

| 技能 | 能力 |
|------|------|
| security-scan | 安全扫描（OWASP 攻击面）|
| secrets-scan | 密钥扫描（凭据泄漏检测）|
| config-scan | 配置扫描（硬编码/敏感配置）|
| dependency-scan | 依赖扫描（漏洞/许可证）|

#### P.3 全局规则（2）

| 技能 | 能力 |
|------|------|
| core-rules | 全局规则（密码安全/权限确认/长任务反馈/session 维护）**（退役：真源保留、链接已摘——硬约束迁用户级 memory，②③废弃，④并入交接）**|
| version-management | **通用版本管理**（SemVer 定号 + 单版本源 + CHANGELOG + 发布标记；兼容性判定/弃用政策/不可变发布；**不依赖 VCS**，无 git 也可用）|

#### P.4 协作（7）

| 技能 | 能力 |
|------|------|
| project-handoff | 交接文档（引用型 delta **5 节 + ≤1K token 硬预算**——交接方；环境指纹最小化接手复验）|
| project-intake | 项目接手（读 HANDOFF 恢复上下文；**指纹门控：环境未变即跳过复验**——接收方）|
| decision-log | **决策日志（ADR）**（Nygard 模板 + proposed/accepted/superseded/rejected 状态机——记录/查询）|
| experiment-handoff | 实验性交接（worktree/branch/copy 隔离 → 交接 → 反馈驱动合并回主；**已挂载、仅用户 `/invoke`（禁 agent 自主）**）|
| task-loop-progress | 长任务进度 loop（config+adapter——轮询/汇报）**（退役：真源保留、链接已摘）**|
| workshop-facilitation | 交互工作坊协议（deanpeters 交互技能配对——session 头/单问轮/进度标签）|
| session-health | 会话健康度评估（压缩/经济/工作性质——继续 vs 新开）**（退役：真源保留、链接已摘）**|

---

## 二、分类统计

| 阶段 | 数量 | 说明 |
|------|------|------|
| ① 发现 | 16 | 用户研究 3 + 问题定义 4 + 市场竞品 7 + 调研纪律 2 |
| ② 定义 | 7 | 定位 2 + 需求规格 4 + 拆解立项 1 |
| ③ 设计 | 23 | 领域建模 9 + 模型评审 2 + 架构 3 + 编码规范 3 + 视觉 6 |
| ④ 交付 | 23 | 计划 4 + 工程 1 + 测试链 10 + 质量审查 6 + 质询 2 |
| ⑤ 上线 | 1 | 发布 |
| ⑥ 运营 | 2 | 营销 |
| 贯穿层 | 17 | 审计 4 + 安全 4 + 规则 2 + 协作 7 |
| **合计** | **89** ✅ | 全部唯一分类（已核对无重复/无遗漏）|

---

## 三、一图流（子类级）

```text
产品 0-1 全生命周期（21 子类 · 87 技能）
┌──────────────────────────────────────────────────────────────┐
│ ① 发现     1.1 用户研究(3)  1.2 问题定义(4)                  │
│            1.3 市场竞品(7)×8编排  1.4 调研纪律(2)             │
├──────────────────────────────────────────────────────────────┤
│ ② 定义     2.1 定位(2)  2.2 需求规格(4·含主入口)              │
│            2.3 拆解立项(1)                                    │
├──────────────────────────────────────────────────────────────┤
│ ③ 设计     3.1 领域建模DDD(9·链式)  3.2 模型评审(2)           │
│            3.3 架构设计(3)  3.4 编码规范(3)  3.5 视觉设计(6)   │
├──────────────────────────────────────────────────────────────┤
│ ④ 交付     4.1 计划执行(4·含 stage-spec)  4.2 工程协作(1)     │
│            4.3 测试链(10·含 coverage-matrix)  4.4 质量审查(6·含 stage-gate/audit-item)  4.5 质询(2)  │
├──────────────────────────────────────────────────────────────┤
│ ⑤ 上线     product-launch · ⑥ 运营  product-marketing · marketing-copywriting  │
├──────────────────────────────────────────────────────────────┤
│ 贯穿       P.1 审计(4·含 skill-eval/skill-fit)  P.2 安全(4)  P.3 规则(2·含 core-rules/version-management)  P.4 协作(7·含 decision-log/experiment-handoff) │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、新项目启动引导（0-1 按阶段取用）

1. **启动对齐**：`core-rules` 已退役（硬约束改由用户级 memory `~/.commandcode/AGENTS.md` 常驻；工作区事实见工作区根 `AGENTS.md`）→ 1.1 `delegated-research`（调研）
2. **发现**：1.1 `user-research` / `discovery-interview-prep` → 1.2 `problem-statement` → `jobs-to-be-done` → `proto-persona` → `customer-journey-map`；竞品走 1.3 `competitive-analysis-process`（编排 ×8）
3. **定义**：2.1 `positioning-workshop` → `positioning-statement` → 2.2 `write-spec` / `prd-development` → `prd-driven-ddd`（主入口）→ 2.3 `to-tickets`（拆解）
4. **设计**：3.1 `prd-driven-ddd` 链式调 `ddd-scope→discover→subdomains→contexts→context-map→aggregates→domain-interactions→openspec-bridge`；3.3 `architecture-patterns` + `codebase-design`；3.4 规范三件套；3.5 视觉 `frontend-design` + `ui-ux-pro-max`
5. **交付**：4.1 `roadmap-planning` → **阶段制**：开工前 `stage-spec`（阶段契约）→ 需要时 `writing-plans`（任务分解）→ `executing-plans`（执行）→ 阶段中裁定 `decision-log`（ADR）→ 阶段末 `coverage-matrix`（S2 起）→ 4.4 `code-review`（阶段末即时评审模式）→ 声称完成 → **`stage-gate` 跑 DoD 门禁**（含 `audit-item` open 项核对）；遇问题走 `problem-handling`（诊断→分级→处置→收尾），代码根因路径内用 `systematic-debugging`
6. **验收**：P.1 `product-doc-audit`（四层 go/no-go）+ P.2 安全四件套 + 3.2 `ddd-model-review` + 4.3 `k6-performance`（性能）
7. **上线/交接**：⑤ `product-launch` + ⑥ `product-marketing` → P.4 `project-handoff` → 下一位 `project-intake`

**规则**：阶段产物格式对齐下阶段技能（PRD 的 AC → to-tickets 的 predicates）；交付前必跑质量链。

---

## 五、使用建议

- **新项目启动**：按阶段取技能（①→⑥）——阶段间产物自然传递（研究→PRD→领域模型→tickets→实现→验收）
- **质量门禁**：交付前跑 ddd-qa-chain 全链 + product-doc-audit（含项目最终验收）；阶段制项目走「阶段门禁链」（7.1：stage-spec → 执行 → stage-gate 跑 DoD + audit-item 核对）
- **技能审计**：新接入技能 → 审计（description 合规）+ 本图更新（分类/计数/一图同步）
- **克制原则**：只接高价值技能（多源验证 + 实物克隆）；二级语义引用标注不接入

---

## 六、语义引用说明（未接入的可选参考——2026-08-02）

为保持技能库克制（89 技能），以下**二级语义引用未接入**（deanpeters 同库可选参考——各技能正文已加「相关技能说明」标注）：

- **tam-sam-som-calculator**（被 market-landscape-scan / competitive-research-snapshot / intelligence-collection-disciplines / company-intel 引用——市场量化）
- **company-research**（被 competitive-research-snapshot / intelligence-collection-disciplines / company-intel 引用）
- **pestel-analysis**（被 competitive-intel-watch / company-intel 引用）
- **derisk-measurement-advisor / business-health-diagnostic / acquisition-channel-advisor**（company-intel 引用）
- **opportunity-solution-tree**（voice-of-customer-miner 引用）
- **refactoring**（wondel Fowler 目录——无直源——现有 code-review/codebase-design/ddd-tactical-review 组合覆盖重构操作——需要时自建）
- **discovery-process / problem-framing-canvas / customer-journey-mapping-workshop**（prd-development 引用——发现/问题框定输入，现有 user-research / discovery-interview-prep / problem-statement / customer-journey-map 组合覆盖）
- **epic-hypothesis**（jobs-to-be-done / prd-development 引用——epic 假设结构化，现有 to-tickets 拆解覆盖）
- **user-story / user-story-mapping / user-story-mapping-workshop**（problem-statement / proto-persona / customer-journey-map / prd-development 引用——用户故事拆解，现有 to-tickets 覆盖）
- **prioritization-advisor / product-strategy-session**（roadmap-planning 引用——优先级与策略前置，现有 roadmap-planning 内置 RICE 框架 + positioning-statement 覆盖）

**情况说明**：引用仅为参考方向（不阻塞独立使用）；实际需要时按需接入对应技能。

---

## 七、子类分析（2026-08-02 · 基于 21 子类）

### 7.1 编排路径（子类间链式调用）

| 场景 | 编排路径 |
|------|---------|
| **新项目主链** | 1.1→1.2→2.1→2.2（主入口 prd-driven-ddd）→3.1（DDD 链 8 步）→2.3→4.1→4.3→P.1 |
| **竞争分析链** | 1.3 `competitive-analysis-process` 编排 ×8（景观→快照→VoC→公司→监测→战斗卡）|
| **质量门禁链** | 4.3 测试（L1-L5）→4.4 审查→P.1 文档审计→P.2 安全四件套→3.2 模型评审 |
| **阶段门禁链** | 4.1 `stage-spec`（契约）→ `writing-plans`/`executing-plans`（执行）→ 裁定 `decision-log`（ADR）→ 阶段末 `coverage-matrix` + 4.4 `code-review`（阶段评审→发现入 `audit-item`）→ **`stage-gate` 跑 DoD**（open 项核对）→ 下一阶段 |
| **问题处理链** | 4.4 `problem-handling`（诊断→分级→处置→收尾；代码根因路径内用 `systematic-debugging`）|
| **重构操作链** | 4.4 code-review（发现 smells）→3.3 codebase-design（设计目标）→3.2 tactical-review（领域重构）|
| **交接链** | P.4 handoff（写 delta）→ intake（读 delta 恢复）——工具/会话切换 |

### 7.2 组合模式（子类成组使用）

| 组合 | 构成 | 场景 |
|------|------|------|
| **定义闭环** | 2.1 + 2.2 + 2.3 | 定位→PRD→tickets（一次定清楚）|
| **阶段门禁组合** | 4.1 stage-spec + decision-log（P.4）+ 4.4 code-review（阶段评审）+ audit-item + stage-gate | 阶段开工契约 → 阶段中裁定 → 阶段末评审 → 门禁收口（7.1 阶段门禁链）|
| **架构三件套** | 3.3（patterns/design/analysis）| 设计→深化→分析（新模块）|
| **规范三件套** | 3.4（ts/react/electron）| 前端工程规范（我们栈）|
| **QA 全家当** | 4.3 全部 9 | 全量质量验证（交付前）|
| **验收组合** | P.1 + P.2 + 3.2 | 文档 + 安全 + 模型——最终 go/no-go |
| **上线组合** | ⑤ product-launch + ⑥ product-marketing + P.4 | 发布→营销→交接 |

### 7.3 薄弱子类（1 技能——单体但关键）

| 子类 | 技能 | 关键性 |
|------|------|--------|
| 2.3 拆解立项 | to-tickets | ⭐⭐⭐ 需求→任务（AI-ready AC）|
| 4.2 工程协作 | git-workflow | ⭐⭐ 提交一致性 |
| ⑤ 上线 | product-launch | ⭐⭐⭐ 发布全流程 |
| P.3 规则 | version-management | ⭐⭐⭐ 版本一致性底线（core-rules 已退役）|

**说明**：薄弱子类均为单体高价值（无需扩展——多则冗余）；4.2 可考虑补 pre-commit 钩子类（mattpocock setup-pre-commit——已见未接——低优先）。

### 7.4 覆盖度观察

- **测试侧最厚**（4.3 测试链十技能 + 4.4 stage-gate 聚合验证 + P.2 四件套）——质量保证优先——符合产品交付观
- **上线/运营最薄**（1+2）——符合现状（项目未到上线期）——上线前再评估
- **二级语义引用 6 个**（克制保持）——需要时按需接入

---

## 八、技能版本索引（frontmatter `version` · SkillHub 发布版本）

> 本表是**版本索引**（版本唯一源仍是各包 frontmatter 顶层 `version`）；一致性由 `bash scripts/check-index.py` 校验，漂移即门禁失败。规则说明见 [`README.md`](README.md)「版本规范」。

| 技能 | 版本 | 技能 | 版本 | 技能 | 版本 |
|------|------|------|------|------|------|
| `accessibility-auditor` | 1.0.0 | `api-contract-validator` | 1.0.0 | `architecture-patterns` | 1.0.0 |
| `audit-item` | 1.0.0 | `autonomous-investigation` | 1.0.0 | `battle-card-builder` | 1.0.0 |
| `cicd-pipeline` | 1.0.0 | `code-review` | 1.0.1 | `codebase-design` | 1.0.0 |
| `company-intel` | 1.0.1 | `competitive-analysis-process` | 1.0.0 | `competitive-intel-watch` | 1.0.0 |
| `competitive-research-snapshot` | 1.0.0 | `config-scan` | 1.0.0 | `core-rules` | 1.1.0 |
| `coverage-matrix` | 1.0.0 | `customer-journey-map` | 1.0.0 | `ddd-aggregates` | 1.0.0 |
| `ddd-context-map` | 1.0.0 | `ddd-contexts` | 1.0.0 | `ddd-discover` | 1.0.0 |
| `ddd-domain-interactions` | 1.0.0 | `ddd-model-review` | 1.0.0 | `ddd-openspec-bridge` | 1.0.0 |
| `ddd-qa-chain` | 1.0.0 | `ddd-scope` | 1.0.0 | `ddd-subdomains` | 1.0.0 |
| `ddd-tactical-review` | 1.0.0 | `decision-log` | 1.0.0 | `deep-codebase-analysis` | 1.0.0 |
| `delegated-research` | 1.0.0 | `dependency-scan` | 1.0.0 | `discovery-interview-prep` | 1.0.0 |
| `electron-best-practices` | 1.0.0 | `event-storming` | 1.0.0 | `executing-plans` | 1.0.1 |
| `frontend-design` | 1.0.0 | `git-workflow` | 1.0.0 | `grill-me` | 1.0.0 |
| `intelligence-collection-disciplines` | 1.0.0 | `jobs-to-be-done` | 1.0.0 | `k6-performance` | 1.0.0 |
| `market-landscape-scan` | 1.0.0 | `marketing-copywriting` | 1.0.0 | `pixel-perfect` | 1.0.0 |
| `plan-grilling` | 1.0.0 | `playwright-best-practices` | 1.0.0 | `positioning-statement` | 1.0.0 |
| `positioning-workshop` | 1.0.0 | `prd-development` | 1.0.0 | `prd-driven-ddd` | 4.5.4 |
| `press-release` | 1.0.0 | `problem-handling` | 1.0.1 |  |  |
| `problem-statement` | 1.0.0 | `product-doc-audit` | 1.0.0 | `product-launch` | 1.0.0 |
| `product-marketing` | 1.0.0 | `project-handoff` | 1.3.0 | `project-intake` | 1.3.0 |
| `proto-persona` | 1.0.0 | `react-vite-best-practices` | 1.0.2 | `roadmap-planning` | 1.0.0 |
| `secrets-scan` | 1.0.0 | `security-scan` | 1.0.0 | `session-health` | 1.0.0 |
| `skill-description-audit` | 1.9.1 | `skill-eval` | 1.0.0 | `stage-gate` | 1.0.0 |
| `stage-spec` | 1.0.0 | `systematic-debugging` | 1.0.2 | `task-loop-progress` | 1.0.0 |
| `test-data-generation` | 1.0.0 | `to-tickets` | 1.0.0 | `typescript-best-practices` | 1.0.0 |
| `ui-animation` | 1.0.0 | `ui-typography` | 1.0.0 | `ui-ux-pro-max` | 1.0.0 |
| `user-research` | 1.0.0 | `ux-heuristics` | 1.0.0 | `verification-before-completion` | 1.0.1 |
| `visual-regression-tester` | 1.0.0 | `voice-of-customer-miner` | 1.0.0 | `web-design-guidelines` | 1.0.0 |
| `workshop-facilitation` | 1.0.0 | `write-spec` | 1.0.0 | `writing-plans` | 1.0.1 |
| `experiment-handoff` | 1.0.2 | `skill-fit` | 1.2.1 | `version-management` | 1.2.0 |


