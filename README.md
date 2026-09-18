# Agent Skills

[![skills.sh](https://skills.sh/b/NinjaSln-labs/agent-skills)](https://skills.sh/NinjaSln-labs/agent-skills)

**[English](README.en.md) | 中文**

> 便携式 Agent Skill 集合（遵循 [Agent Skills](https://agentskills.io) 开放规范，`SKILL.md`），可安装到任何支持该规范的 AI 编码代理（Claude Code / Cursor / Deep Code / Copilot CLI 等）。

共 **89 个技能**，覆盖产品 0-1 全生命周期（发现 → 定义 → 设计 → 交付 → 上线 → 运营），以及 DDD、工程、QA、安全、UI/UX 贯穿层。每个技能 = 一个目录 + `SKILL.md`（frontmatter `name`/`description` + 正文），渐进式披露（正文 <500 行，深内容走 `references/`）。

技能全景图（按产品 0-1 阶段分类 + 编排路径，含「阶段门禁链」「问题处理链」等跨技能编排）见 [SKILLS-MAP.md](SKILLS-MAP.md)。

## 快速开始

```bash
npx skills add NinjaSln-labs/agent-skills   # skills.sh 一键安装全部 89 个技能
```

```bash
git clone https://github.com/NinjaSln-labs/agent-skills.git
cd agent-skills

# 安装单个技能（拷贝到代理的技能发现根目录）
cp -r <skill-name> ~/.agents/skills/
# 或安装全部技能
for d in */; do cp -r "$d" ~/.agents/skills/; done
```

安装后重启/重载代理客户端，技能即可被发现。用户级目录为 `~/.agents/skills/`，项目级为 `<项目>/.agents/skills/`。

## 技能清单

### 工程实践（21）

| 技能 | 说明 |
|------|------|
| architecture-patterns | Clean/Hexagonal/DDD 实现架构（依赖规则/端口适配器） |
| audit-item | 审计问题 issue 化跟踪（NNN-slug + 索引——open/fixed/recorded，被 stage-gate 枚举） |
| cicd-pipeline | CI/CD 配置（GitHub Actions/Jenkins/GitLab CI） |
| code-review | 代码审查（diff/PR——bug/风格/约定 + 阶段末即时评审模式：固定点=阶段首 commit^、状态化 open/fixed/rec… |
| codebase-design | 深度模块设计（接口/接缝/可测试性——mattpocock） |
| deep-codebase-analysis | 代码库全面分析（架构/通信/模式/约定/业务流/状态/错误处理 7 维） |
| electron-best-practices | Electron 最佳实践（主/渲染进程/安全/打包） |
| frontend-design | 前端设计（组件/页面——两遍法+自评） |
| git-workflow | Git 工作流（分支策略/Conventional Commits/CI 集成——37★） |
| react-vite-best-practices | React + Vite 最佳实践（组件/性能/工程） |
| systematic-debugging | 系统化调试（假设/二分/证据——代码缺陷路径） |
| problem-handling | 问题处理单链（诊断→严重度分级→workaround/永久修复→TDD 修复→验证→无责收尾+known-error… |
| typescript-best-practices | TS 最佳实践（类型/模式/工程规范） |
| version-management | 通用版本管理（SemVer 定号 + 单版本源 + CHANGELOG + 发布标记；兼容性判定/弃用政策/不可变发布… |
| verification-before-completion | 完成前验证（行为保持——规范） |
| stage-gate | 阶段门禁执行（读 stage-spec DoD 逐条验证——L1/L2/L3/行为验收/覆盖矩阵/审计项/push——只验不修） |
| stage-spec | 阶段契约编写/回填（DoD 机器可验证断言 + TDD 网格 + 边界——被 stage-gate 执行） |
| writing-plans | 实施计划编写（任务拆解/文件路径/验证步骤） |
| write-spec | 规格编写（背景/范围/成功标准/接口契约） |
| executing-plans | 计划执行（加载→批判性审查→逐任务执行→汇报） |
| to-tickets | 需求拆解为 ticket（垂直切片 + AI-ready 验收标准 predicates） |

### DDD / 领域驱动设计（13）

| 技能 | 说明 |
|------|------|
| ddd-aggregates | 聚合设计（不变量/边界/事务） |
| ddd-context-map | 上下文映射（集成模式/契约所有权/失败模式） |
| ddd-contexts | 限界上下文 + 通用语言 + 边界 ADR |
| ddd-discover | 领域发现（事件流/命令/热点/歧义） |
| ddd-domain-interactions | 领域交互（事件/服务/仓储/工厂） |
| ddd-model-review | 模型质量评估（一致性/完整性/耦合——回溯触发） |
| ddd-openspec-bridge | DDD → OpenSpec 桥接（结构化规范） |
| ddd-qa-chain | 质量链编排（L1 单测→L2 契约→L3 组件→L4 E2E→L5 视觉 + DoD 门禁——层概念通用，工具命令按项目映射探测… |
| ddd-scope | DDD 范围收敛（问题陈述/目标/约束/术语种子/风险） |
| ddd-subdomains | 子域分类（Core/Supporting/Generic） |
| ddd-tactical-review | 战术 DDD 评审（贫血模型检测/富领域重构） |
| event-storming | EventStorming 工作坊（Big Picture/Process/Design-Level） |
| prd-driven-ddd | PRD 驱动 DDD 主入口（场景验证→架构映射→落地链路） |

### 产品 / PM（26）

| 技能 | 说明 |
|------|------|
| autonomous-investigation | 自主调研（Fact/Inference/Assumption 证据纪律） |
| battle-card-builder | 战斗卡（竞争分析 Step7 产出） |
| company-intel | 公司情报（财务/组织/渠道——Step4——11 节输出） |
| competitive-analysis-process | 六步竞争分析（编排——景观→战略方向） |
| competitive-intel-watch | 竞品方向监测（TECHINT/HUMINT/FININT/MASINT 融合——Step6 节奏） |
| competitive-research-snapshot | 竞品快照（产品对比矩阵——Step2） |
| customer-journey-map | 客户旅程地图（阶段/触点/情绪/机会） |
| discovery-interview-prep | 发现访谈准备（问题设计/防引导） |
| grill-me | 计划/设计质询（用户触发——执行前压力测试） |
| plan-grilling | 计划/设计质询（用户触发——执行前压力测试） |
| intelligence-collection-disciplines | 情报收集纪律（SIGINT/HUMINT/FININT/MASINT/TECHINT 通道） |
| jobs-to-be-done | JTBD 任务映射（场景→需求→验收） |
| product-launch | 产品发布（ORB 框架 + 五阶段 + Product Hunt 策略 + 清单） |
| market-landscape-scan | 市场景观扫描（细分/玩家/动态/空白——Step1） |
| positioning-statement | 定位陈述（对谁/解决什么/为何不同） |
| positioning-workshop | 定位工作坊（多候选→收敛） |
| prd-development | PRD 开发（上下文/目标/用户故事/验收） |
| press-release | 新闻稿式产品定义（亚马逊逆向工作法） |
| problem-statement | 问题陈述（单句痛点 + 证据锚点） |
| product-doc-audit | 产品文档集审计（三层 + 就绪度评分 + 四层 go/no-go 最终验收） |
| product-marketing | 产品营销上下文（.agents/product-marketing.md 共享语境） |
| proto-persona | 原型人物（实证锚定——防虚构画像） |
| roadmap-planning | 产品路线图规划（目标/里程碑/优先级） |
| user-research | 用户研究（招募/访谈/证据分级） |
| voice-of-customer-miner | 客户之声挖掘（评论/社区——需求满足度——Step3） |
| workshop-facilitation | 交互工作坊协议（deanpeters 交互技能配对——session 头/单问轮/进度标签） |

### 测试 / QA（9）

| 技能 | 说明 |
|------|------|
| accessibility-auditor | 可及性审计（WCAG 2.1 AA——axe + 键盘/焦点） |
| api-contract-validator | API 契约验证（OpenAPI/JSON Schema/消费者契约） |
| coverage-matrix | 覆盖矩阵（不变量↔测试 / 事件↔测试 / DoD↔门禁 三向表 + 缺口入审计项） |
| dependency-scan | 依赖扫描（漏洞/许可证） |
| k6-performance | 性能测试（k6——阈值/场景/自定义指标） |
| playwright-best-practices | Playwright 最佳实践（选择器/断言/稳定性） |
| pixel-perfect | 视觉回归（像素对比——默认免费） |
| test-data-generation | 测试数据生成（Faker/工厂/构建器/种子） |
| visual-regression-tester | 视觉回归（双路线——Playwright 免费 + Chromatic/Percy 商业） |

### 安全（3）

| 技能 | 说明 |
|------|------|
| config-scan | 配置扫描（硬编码/敏感配置） |
| secrets-scan | 密钥扫描（凭据泄漏检测） |
| security-scan | 安全扫描（OWASP 攻击面） |

### UI/UX 与内容（6）

| 技能 | 说明 |
|------|------|
| ui-ux-pro-max | UI/UX 交互设计（设计系统/一致性） |
| web-design-guidelines | Web 设计规范（排版/色彩/可及性——WebFetch 降级） |
| ui-animation | 设计工程与动效决策（Emil Kowalski——动画框架/组件原则/隐形细节） |
| ui-typography | 专业排版规则（引号/破折号/间距/层级——ENFORCEMENT+AUDIT 双模式——Butterick） |
| ux-heuristics | 可用性启发式审计（Nielsen 10/Krug 定律/严重度评级——wondelai v1.6.0） |
| marketing-copywriting | 营销文案（价值主张/情感/转化——15 节） |

### Agent 会话与个人效率（11）

| 技能 | 说明 |
|------|------|
| project-handoff | 交接文档（引用型 delta 5 节 + ≤1K token 硬预算——交接方；环境指纹最小化接手复验） |
| project-intake | 项目接手（读 HANDOFF 恢复上下文；指纹门控：环境未变即跳过复验——接收方） |
| experiment-handoff | 实验性交接（worktree/branch/copy 隔离 → 交接 → 反馈驱动合并回主… |
| decision-log | 决策日志（ADR）（Nygard 模板 + proposed/accepted/superseded/rejected 状态机——记录/查询… |
| delegated-research | 通用调研（广度→深度→核实——证据链） |
| session-health | 会话健康度评估（压缩/经济/工作性质——继续 vs 新开）（已废弃） |
| core-rules | 全局规则（密码安全/权限确认/长任务反馈/session 维护）（已废弃） |
| skill-description-audit | 技能描述审计（description↔正文交叉验证 + 结构/语言/名称/误触发防护 + pushy 质量… |
| skill-eval | skill 行为评估（3-5 代表任务 × 有/无 skill N≥3 次 → pass-rate 对比表 + 失败案例反哺） |
| skill-fit | 技能适配管家（按项目画像对照 catalog.yaml 出「建议挂/建议摘/缺口」三清单；只读 v1… |
| task-loop-progress | 长任务进度 loop（config+adapter——轮询/汇报）（已废弃） |

## 已废弃（Deprecated）

以下名称已更名或合并，不再单独发布（旧名不可复用）：

| 旧名 | 现状 |
|------|------|
| `animation` | 已更名至 `ui-animation` |
| `typography` | 已更名至 `ui-typography` |
| `grilling` | 已更名至 `plan-grilling` |
| `launch` | 已更名至 `product-launch` |
| `copywriting` | 已更名至 `marketing-copywriting` |
| `research` | 已更名至 `delegated-research` |
| `sin-rules` | 已更名至 `core-rules` |
| `problem-dive` | 已合并至 `problem-handling` |
| `problem-resolution-flow` | 已合并至 `problem-handling` |

## 目录结构

```
<skill-name>/
├── SKILL.md          # 技能定义（frontmatter name/description + 正文）
├── references/       # 渐进式披露参考文档（按需加载）
├── scripts/          # 辅助脚本
├── templates/        # 模板
├── examples/         # 示例
└── evals/            # 评估用例
```

## License

各技能自带 `license` 字段（多为 MIT / CC-BY-SA-4.0），以各 `SKILL.md` frontmatter 为准。
