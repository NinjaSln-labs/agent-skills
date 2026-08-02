# 技能库全景图（76 技能——产品 0-1 全阶段模式）

- 日期：2026-08-02 · 全量审计 76/76 合规
- 覆盖：本仓库 `agent-skills` 的 76 个技能（可安装到 `~/.agents/skills/<name>`）
- 模式：**产品 0-1 全生命周期**（发现 → 定义 → 设计 → 交付 → 上线 → 运营）+ 贯穿层（质量/工程/协作/技能基建）

---

## 一、按阶段分类

### ① 发现（16）—— 问题 / 市场 / 用户 / 竞品

#### 1.1 用户研究（3）

| 技能 | 能力 |
|------|------|
| user-research | 用户研究（招募/访谈/证据分级）|
| research | 通用调研（广度→深度→核实——证据链）|
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

### ③ 设计（20）—— 领域 / 架构 / 规范 / 视觉

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

#### 3.5 视觉设计（3）

| 技能 | 能力 |
|------|------|
| frontend-design | 前端设计（组件/页面——两遍法+自评）|
| ui-ux-pro-max | UI/UX 交互设计（设计系统/一致性）|
| web-design-guidelines | Web 设计规范（排版/色彩/可及性——WebFetch 降级）|

### ④ 交付（18）—— 计划 / 实现 / 测试 / 质量

#### 4.1 计划执行（3）

| 技能 | 能力 |
|------|------|
| writing-plans | 实施计划编写（任务拆解/文件路径/验证步骤）|
| executing-plans | 计划执行（加载→批判性审查→逐任务执行→汇报）|
| roadmap-planning | 产品路线图规划（目标/里程碑/优先级）|

#### 4.2 工程协作（1）

| 技能 | 能力 |
|------|------|
| git-workflow | Git 工作流（分支策略/Conventional Commits/CI 集成——37★）|

#### 4.3 测试链（9）

| 技能 | 能力 |
|------|------|
| ddd-qa-chain | 质量链编排（L1 单测→L2 契约→L3 组件→L4 E2E→L5 视觉 + DoD 门禁）|
| playwright-best-practices | Playwright 最佳实践（选择器/断言/稳定性）|
| pixel-perfect | 视觉回归（像素对比——默认免费）|
| visual-regression-tester | 视觉回归（双路线——Playwright 免费 + Chromatic/Percy 商业）|
| accessibility-auditor | 可及性审计（WCAG 2.1 AA——axe + 键盘/焦点）|
| api-contract-validator | API 契约验证（OpenAPI/JSON Schema/消费者契约）|
| k6-performance | 性能测试（k6——阈值/场景/自定义指标）|
| test-data-generation | 测试数据生成（Faker/工厂/构建器/种子）|
| cicd-pipeline | CI/CD 配置（GitHub Actions/Jenkins/GitLab CI）|

#### 4.4 质量审查（3）

| 技能 | 能力 |
|------|------|
| code-review | 代码审查（diff/PR——bug/风格/约定——mattpocock）|
| verification-before-completion | 完成前验证（行为保持——规范）|
| systematic-debugging | 系统化调试（假设/二分/证据）|

#### 4.5 质询（2）

| 技能 | 能力 |
|------|------|
| grilling / grill-me | 计划/设计质询（用户触发——执行前压力测试）|

### ⑤ 上线（1）

| 技能 | 能力 |
|------|------|
| launch | 产品发布（ORB 框架 + 五阶段 + Product Hunt 策略 + 清单）|

### ⑥ 运营（2）

| 技能 | 能力 |
|------|------|
| product-marketing | 产品营销上下文（.agents/product-marketing.md 共享语境）|
| copywriting | 营销文案（价值主张/情感/转化——15 节）|

### 贯穿层（12）—— 质量 / 工程 / 协作 / 技能基建

#### P.1 技能基建 / 审计（2）

| 技能 | 能力 |
|------|------|
| skill-description-audit | 技能描述审计（description↔正文交叉验证——自审只出报告）|
| product-doc-audit | 产品文档集审计（三层 + 就绪度评分 + 四层 go/no-go 最终验收）|

#### P.2 安全（4）

| 技能 | 能力 |
|------|------|
| security-scan | 安全扫描（OWASP 攻击面）|
| secrets-scan | 密钥扫描（凭据泄漏检测）|
| config-scan | 配置扫描（硬编码/敏感配置）|
| dependency-scan | 依赖扫描（漏洞/许可证）|

#### P.3 全局规则（1）

| 技能 | 能力 |
|------|------|
| sin-rules | 全局规则（密码安全/权限确认/长任务反馈/session 维护）|

#### P.4 协作（5）

| 技能 | 能力 |
|------|------|
| project-handoff | 交接文档（引用型 delta 6 节——交接方）|
| project-intake | 项目接手（读 HANDOFF 恢复上下文——接收方）|
| task-loop-progress | 长任务进度 loop（config+adapter——轮询/汇报）|
| workshop-facilitation | 交互工作坊协议（deanpeters 交互技能配对——session 头/单问轮/进度标签）|
| session-health | 会话健康度评估（压缩/经济/工作性质——继续 vs 新开）|

---

## 二、分类统计

| 阶段 | 数量 | 说明 |
|------|------|------|
| ① 发现 | 16 | 用户研究 3 + 问题定义 4 + 市场竞品 7 + 调研纪律 2 |
| ② 定义 | 7 | 定位 2 + 需求规格 4 + 拆解立项 1 |
| ③ 设计 | 20 | 领域建模 9 + 模型评审 2 + 架构 3 + 编码规范 3 + 视觉 3 |
| ④ 交付 | 18 | 计划 3 + 工程 1 + 测试链 9 + 质量审查 3 + 质询 2 |
| ⑤ 上线 | 1 | 发布 |
| ⑥ 运营 | 2 | 营销 |
| 贯穿层 | 12 | 审计 2 + 安全 4 + 规则 1 + 协作 5 |
| **合计** | **76** ✅ | 全部唯一分类（已核对无重复/无遗漏）|

---

## 三、一图流（子类级）

```text
产品 0-1 全生命周期（21 子类 · 76 技能）
┌──────────────────────────────────────────────────────────────┐
│ ① 发现     1.1 用户研究(3)  1.2 问题定义(4)                  │
│            1.3 市场竞品(7)×8编排  1.4 调研纪律(2)             │
├──────────────────────────────────────────────────────────────┤
│ ② 定义     2.1 定位(2)  2.2 需求规格(4·含主入口)              │
│            2.3 拆解立项(1)                                    │
├──────────────────────────────────────────────────────────────┤
│ ③ 设计     3.1 领域建模DDD(9·链式)  3.2 模型评审(2)           │
│            3.3 架构设计(3)  3.4 编码规范(3)  3.5 视觉设计(3)   │
├──────────────────────────────────────────────────────────────┤
│ ④ 交付     4.1 计划执行(3)  4.2 工程协作(1)                   │
│            4.3 测试链(9·L1-L5)  4.4 质量审查(3)  4.5 质询(2)   │
├──────────────────────────────────────────────────────────────┤
│ ⑤ 上线     launch · ⑥ 运营  product-marketing · copywriting  │
├──────────────────────────────────────────────────────────────┤
│ 贯穿       P.1 审计(2)  P.2 安全(4)  P.3 规则(1)  P.4 协作(5) │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、新项目启动引导（0-1 按阶段取用）

1. **启动对齐**：P.3 `sin-rules` → 1.1 `research`（调研）
2. **发现**：1.1 `user-research` / `discovery-interview-prep` → 1.2 `problem-statement` → `jobs-to-be-done` → `proto-persona` → `customer-journey-map`；竞品走 1.3 `competitive-analysis-process`（编排 ×8）
3. **定义**：2.1 `positioning-workshop` → `positioning-statement` → 2.2 `write-spec` / `prd-development` → `prd-driven-ddd`（主入口）→ 2.3 `to-tickets`（拆解）
4. **设计**：3.1 `prd-driven-ddd` 链式调 `ddd-scope→discover→subdomains→contexts→context-map→aggregates→domain-interactions→openspec-bridge`；3.3 `architecture-patterns` + `codebase-design`；3.4 规范三件套；3.5 视觉 `frontend-design` + `ui-ux-pro-max`
5. **交付**：4.1 `roadmap-planning` → `writing-plans` → `executing-plans` → 4.2 按 `git-workflow` 提交 → 4.3 `ddd-qa-chain`（L1-L5）→ 4.4 `code-review` → `verification-before-completion`
6. **验收**：P.1 `product-doc-audit`（四层 go/no-go）+ P.2 安全四件套 + 3.2 `ddd-model-review` + 4.3 `k6-performance`（性能）
7. **上线/交接**：⑤ `launch` + ⑥ `product-marketing` → P.4 `project-handoff` → 下一位 `project-intake`

**规则**：阶段产物格式对齐下阶段技能（PRD 的 AC → to-tickets 的 predicates）；交付前必跑质量链。

---

## 五、使用建议

- **新项目启动**：按阶段取技能（①→⑥）——阶段间产物自然传递（研究→PRD→领域模型→tickets→实现→验收）
- **质量门禁**：交付前跑 ddd-qa-chain 全链 + product-doc-audit（含项目最终验收）
- **技能审计**：新接入技能 → 审计（description 合规）+ 本图更新（分类/计数/一图同步）
- **克制原则**：只接高价值技能（多源验证 + 实物克隆）；二级语义引用标注不接入

---

## 六、语义引用说明（未接入的可选参考——2026-08-02）

为保持技能库克制（76 技能），以下**二级语义引用未接入**（deanpeters 同库可选参考——各技能正文已加「相关技能说明」标注）：

- **tam-sam-som-calculator**（被 market-landscape-scan / competitive-research-snapshot / intelligence-collection-disciplines / company-intel 引用——市场量化）
- **company-research**（被 competitive-research-snapshot / intelligence-collection-disciplines / company-intel 引用）
- **pestel-analysis**（被 competitive-intel-watch / company-intel 引用）
- **derisk-measurement-advisor / business-health-diagnostic / acquisition-channel-advisor**（company-intel 引用）
- **opportunity-solution-tree**（voice-of-customer-miner 引用）
- **refactoring**（wondel Fowler 目录——无直源——现有 code-review/codebase-design/ddd-tactical-review 组合覆盖重构操作——需要时自建）

**情况说明**：引用仅为参考方向（不阻塞独立使用）；实际需要时按需接入对应技能。

---

## 七、子类分析（2026-08-02 · 基于 21 子类）

### 7.1 编排路径（子类间链式调用）

| 场景 | 编排路径 |
|------|---------|
| **新项目主链** | 1.1→1.2→2.1→2.2（主入口 prd-driven-ddd）→3.1（DDD 链 8 步）→2.3→4.1→4.3→P.1 |
| **竞争分析链** | 1.3 `competitive-analysis-process` 编排 ×8（景观→快照→VoC→公司→监测→战斗卡）|
| **质量门禁链** | 4.3 测试（L1-L5）→4.4 审查→P.1 文档审计→P.2 安全四件套→3.2 模型评审 |
| **重构操作链** | 4.4 code-review（发现 smells）→3.3 codebase-design（设计目标）→3.2 tactical-review（领域重构）|
| **交接链** | P.4 handoff（写 delta）→ intake（读 delta 恢复）——工具/会话切换 |

### 7.2 组合模式（子类成组使用）

| 组合 | 构成 | 场景 |
|------|------|------|
| **定义闭环** | 2.1 + 2.2 + 2.3 | 定位→PRD→tickets（一次定清楚）|
| **架构三件套** | 3.3（patterns/design/analysis）| 设计→深化→分析（新模块）|
| **规范三件套** | 3.4（ts/react/electron）| 前端工程规范（我们栈）|
| **QA 全家当** | 4.3 全部 9 | 全量质量验证（交付前）|
| **验收组合** | P.1 + P.2 + 3.2 | 文档 + 安全 + 模型——最终 go/no-go |
| **上线组合** | ⑤ launch + ⑥ product-marketing + P.4 | 发布→营销→交接 |

### 7.3 薄弱子类（1 技能——单体但关键）

| 子类 | 技能 | 关键性 |
|------|------|--------|
| 2.3 拆解立项 | to-tickets | ⭐⭐⭐ 需求→任务（AI-ready AC）|
| 4.2 工程协作 | git-workflow | ⭐⭐ 提交一致性 |
| ⑤ 上线 | launch | ⭐⭐⭐ 发布全流程 |
| P.3 规则 | sin-rules | ⭐⭐⭐ 全局底线 |

**说明**：薄弱子类均为单体高价值（无需扩展——多则冗余）；4.2 可考虑补 pre-commit 钩子类（mattpocock setup-pre-commit——已见未接——低优先）。

### 7.4 覆盖度观察

- **测试侧最厚**（4.3 九技能 + P.2 四件套）——质量保证优先——符合产品交付观
- **上线/运营最薄**（1+2）——符合现状（项目未到上线期）——上线前再评估
- **二级语义引用 6 个**（克制保持）——需要时按需接入
