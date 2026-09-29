# Stage Gate 断言类型 × 证据三件套表

> 本附篇自 `stage-gate/SKILL.md` 逐字外置；正文「DoD 断言分类与执行方法」节留有指针，内容以本文件为准。

| 断言类型 | 判定方法 | 证据形式 |
|---------|---------|---------|
| **L1 全量** | `npx vitest run`（工作目录 apps/desktop） | 输出尾部（tests/files/passed/failed）+ exit code；spec 有「新增用例 ≥N 条」时核对用例数 |
| **L2 契约** | `npx tsc -p tsconfig.json --noEmit` + `npx tsc -p tsconfig.main.json --noEmit` 双跑 | 各 0 error 才 PASS；任一有错 → FAIL（列出错误数/首错位置） |
| **L3 交互** | `npx playwright test --project=interaction` | 通过数/总数；spec 有预期计数（如 31/31）时对照——不足即 FAIL |
| **行为验收** | spec 内给出的命令或测试；嵌套子断言逐条执行（有测试文件 → `npx vitest run <file>` 定向跑） | 每条子断言独立 PASS/FAIL + 对应测试输出 |
| **覆盖矩阵** | `docs/tests/coverage-matrix.md` 存在 + 抽查 3 条与测试/注册表一致 | 抽查结果；spec 要求「首版已产出」时核对存在性 |
| **审计状态** | 读 `.scratch/neonforge-v1/audit-items/README.md` 枚举 open 项 → 每条核对是否 fixed/recorded | open 项清单（应为空或全部有关闭证据） |
| **决策日志** | `docs/decisions/000-decision-log.md` 索引最新（本阶段裁定有 ADR 编号） | 索引表尾部 |
| **push 状态** | `git status` 干净 + `git log @{u}..HEAD` 为空（无未 push commit） | git 输出尾部；CI 远端绿若可查（本地查不到 → 未验证） |

**嵌套断言**：行为验收下的 `- [ ]` 子条目逐条执行，不得合并成一条「行为验收通过」。
