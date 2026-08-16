# Agent Skills

个人维护的 Agent Skill 集合，遵循 [Agent Skills](https://agentskills.io) 开放规范（`SKILL.md`），可安装到任何支持该规范的 AI 编码代理。

共 **87 个技能**，覆盖产品 0-1 全生命周期（发现 → 定义 → 设计 → 交付 → 上线），以及 DDD、工程、QA、安全、UI/UX。

技能全景图（按产品 0-1 阶段分类与编排路径）见 [SKILLS-MAP.md](SKILLS-MAP.md)。

## 安装

将技能目录拷贝到代理的技能发现根目录（用户级 `~/.agents/skills/` 或项目级 `.agents/skills/`）：

```bash
git clone https://github.com/NinjaSln-labs/agent-skills.git
# 安装单个技能
cp -r agent-skills/<skill-name> ~/.agents/skills/
# 或安装全部技能
for d in agent-skills/*/; do cp -r "$d" ~/.agents/skills/; done
```

安装后重启/重载代理客户端，技能即可被发现。

## 技能清单

### 工程实践（21）

| 技能 | 说明 |
|------|------|
| architecture-patterns | 架构模式指南 |
| audit-item | 审计发现 issue 化跟踪（open/fixed/recorded，被阶段门禁枚举） |
| cicd-pipeline | CI/CD 管道测试配置 |
| code-review | 代码审查（含阶段末即时评审模式） |
| codebase-design | 代码库设计 |
| deep-codebase-analysis | 深度代码库分析 |
| electron-best-practices | Electron 最佳实践 |
| frontend-design | 前端设计 |
| git-workflow | Git 分支/提交/PR/合并流程 |
| react-vite-best-practices | React + Vite 性能优化 |
| systematic-debugging | 系统性调试（先根因后修复） |
| problem-dive | 问题深挖（证据先行，不直接修） |
| problem-resolution-flow | 问题处理全流程（定位→分级→调研→修复→收尾） |
| typescript-best-practices | TypeScript 最佳实践 |
| verification-before-completion | 完成前验证（证据先于断言） |
| stage-gate | 阶段门禁执行（stage-spec DoD 逐条验证，只验不修） |
| stage-spec | 阶段契约编写（DoD 机器可验证断言 + TDD 网格） |
| writing-plans | 编写实现计划 |
| write-spec | 编写 spec / PRD |
| executing-plans | 执行实现计划 |
| to-tickets | 计划/PRD 拆分为可执行工单 |

### DDD / 领域驱动设计（13）

| 技能 | 说明 |
|------|------|
| ddd-aggregates | 聚合设计 |
| ddd-context-map | 上下文映射 |
| ddd-contexts | 限界上下文 |
| ddd-discover | 领域发现 |
| ddd-domain-interactions | 领域交互 |
| ddd-model-review | 领域模型审查 |
| ddd-openspec-bridge | OpenSpec 桥接 |
| ddd-qa-chain | 质量链（DoD 验证） |
| ddd-scope | 领域范围界定 |
| ddd-subdomains | 子域划分 |
| ddd-tactical-review | 战术设计审查 |
| event-storming | 事件风暴 |
| prd-driven-ddd | PRD 驱动的 DDD 建模 |

### 产品 / PM（26）

| 技能 | 说明 |
|------|------|
| autonomous-investigation | 自主调研 |
| battle-card-builder | 竞品战卡 |
| company-intel | 公司情报 |
| competitive-analysis-process | 竞品分析流程 |
| competitive-intel-watch | 竞争情报监控 |
| competitive-research-snapshot | 竞争调研快照 |
| customer-journey-map | 客户旅程地图 |
| discovery-interview-prep | 发现访谈准备 |
| grill-me / plan-grilling |
| intelligence-collection-disciplines | 情报收集纪律 |
| jobs-to-be-done | JTBD 框架 |
| product-launch |
| market-landscape-scan | 市场格局扫描 |
| positioning-statement / positioning-workshop | 定位陈述/工作坊 |
| prd-development | PRD 开发 |
| press-release | 新闻稿式 PRD |
| problem-statement | 问题陈述 |
| product-doc-audit | 产品文档审计 |
| product-marketing | 产品营销上下文 |
| proto-persona | 原型人物画像 |
| roadmap-planning | 路线图规划 |
| user-research | 用户研究 |
| voice-of-customer-miner | 客户之声挖掘 |
| workshop-facilitation | 工作坊促导 |

### 测试 / QA（9）

| 技能 | 说明 |
|------|------|
| accessibility-auditor | 无障碍合规审计 |
| api-contract-validator | API 契约验证 |
| coverage-matrix | 覆盖矩阵（不变量/事件/DoD ↔ 测试门禁） |
| dependency-scan | 依赖漏洞扫描 |
| k6-performance | k6 性能测试 |
| playwright-best-practices | Playwright 最佳实践 |
| pixel-perfect | 视觉回归（Playwright） |
| test-data-generation | 测试数据生成 |
| visual-regression-tester | 视觉回归测试（Playwright/Chromatic） |

### 安全（3）

| 技能 | 说明 |
|------|------|
| config-scan | 配置安全扫描 |
| secrets-scan | 密钥泄露扫描 |
| security-scan | 综合安全扫描（OWASP Top 10） |

### UI/UX 与内容（6）

| 技能 | 说明 |
|------|------|
| ui-ux-pro-max | UI/UX 设计数据库（84 风格/192 色板/22 栈） |
| web-design-guidelines | Web 界面指南合规审查 |
| ui-animation | 动效设计决策（Emil Kowalski 哲学） |
| ui-typography | 专业排版规则（引号/间距/层级） |
| ux-heuristics | 可用性启发式审计（Nielsen 10） |
| marketing-copywriting | 营销文案写作 |

### Agent 会话与个人效率（9）

| 技能 | 说明 |
|------|------|
| project-handoff | 项目交接文档 |
| project-intake | 项目接手恢复 |
| decision-log | 决策日志 ADR（记录/查询，状态机） |
| delegated-research | 委托式后台调研 |
| session-health | 会话健康度评估 |
| core-rules | 全局规则（密码安全/权限确认/长任务反馈/session 维护） |
| skill-description-audit | 技能描述交叉验证审计 |
| skill-eval | skill 行为评估（有/无 skill pass-rate 对比） |
| task-loop-progress | 长任务进度 Loop |

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


