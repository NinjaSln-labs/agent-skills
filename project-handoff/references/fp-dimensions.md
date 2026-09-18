# 环境指纹维度指南（fp.txt 该放什么）

> 用途：`project-handoff` 正文只留契约；「哪些维度合适、常见误入、各项目类型示例」放这里，按需加载。
> 契约单源：`../SKILL.md`「环境指纹」节；命令 `handoff-lint.sh fp write|check`。

## 一句话判据

一条 fp.txt 项 = 一个「能独立复验的维度」：它变了，接收方就知道该重跑**哪一件事**。
必须同时满足三点，缺一不放：**决定环境是否变化**、**跨接手稳定**、**变了有明确对应的复验动作**。

## 合适（放进 fp.txt）

| 类别 | 写法 | 变化后接收方复验什么 |
|------|------|----------------------|
| 解释器/运行时版本 | `cmd:python3 --version` · `cmd:node --version` | 重装依赖 / 重建 venv |
| 平台与架构 | `cmd:uname -s -m` | 重编原生依赖 / 换二进制 |
| 工具链版本 | `cmd:git --version` · `cmd:docker --version` | 更新工具链相关步骤 |
| 依赖锁定内容 | `file:package-lock.json` · `file:poetry.lock` · `file:requirements.txt` | 重装依赖 |
| 关键运行配置内容 | `file:docker-compose.yml` · `file:.env.example`（**非**含值文件） | 重启服务 / 重配 |

## 易误入（不要放）

| 反例 | 为什么错 |
|------|----------|
| `file:catalog.yaml` · `file:SKILLS-MAP.md` · `file:README.md` | 业务内容，天天变 → 指纹永远「不一致」，门控失效 |
| `cmd:date` · `cmd:git status` · `cmd:git log -1` | 时间 / 仓库状态，非环境；每次必变 |
| 真实含值配置或密钥文件（如 `.env`） | 变动噪音大；即便只存哈希也不建议——改用 `.env.example` 或版本类项 |
| 外部服务探测（如 `cmd:curl -s https://...`） | 网络抖动 → 假「环境变化」，误触发全量复验 |
| 逐条堆砌（10+ 项） | 维度过细；按「可独立复验的维度」聚合 |

## 粒度原则

- **一条对应一个复验动作**：若两项变化后复验动作相同，合并为一条。
- **维度独立**：`fp check` 不一致时按项 diff，接收方只复验变化项——粒度太粗会放大复验范围。

## 各项目类型示例

**纯文档/脚本库（无运行时依赖）**——本库 `.handoff/fp.txt`：

```
cmd:python3 --version
cmd:uname -s -m
cmd:git --version
```

**Node 前端/服务**：

```
cmd:node --version
cmd:pnpm --version
file:pnpm-lock.yaml
```

**Python 服务**：

```
cmd:python3 --version
file:poetry.lock
cmd:docker --version
```

**容器化多服务**：

```
cmd:docker --version
cmd:docker compose version
file:docker-compose.yml
```

## 维护

- 改 `.handoff/fp.txt` 后必须 `handoff-lint.sh fp write` 重写 `.handoff/fp.sha`，否则比对基准过期。
- 指纹与 HANDOFF 正交：HANDOFF 记状态，指纹记环境；`.handoff/fp.sha` 不占 HANDOFF 预算，只存每项 8 位短哈希、**不存值**。
