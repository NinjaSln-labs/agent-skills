# auto-approve 白名单（Q-05）

> skill-fit 权限档升档前置。权威：`design/skill-fit-v2/03-AGGREGATES.md` S-2／INV-11；本文件＝运行时闭集。
> lastUpdated: 2026-09-28 · refreshInterval: 事件触发（白名单增删行／升档裁时修订）· 置信度: 高（现行空表＝全 ask-user，与正文 INV-11／08 前置一致）

## 现行（2.1.0 开闸）

| 动作类型 | 风险档 | 层级 | 权限 | 置信度 |
|---|---|---|---|---|
| （空） | — | — | — | — |

**白名单为空 ⇒ 全部走 `ask-user`**（逐条口令：`yes-this-one`／`no-and-why`／`later`；`all-in-this-class` 仅同类同风险批确认，单条 CLI 拒）。

升 `auto-approve` 前置（08）：确认门留痕达标＋本表白名单至少一行成文。本波实测只产 ask-user 留痕，**不升档**。填第一行起须同步刷新本文件头注 `lastUpdated`。

## 永久排除（INV-11）

下列动作类型**永不**入白名单，即使日后升档：

- 凭据／密钥／token 相关技能的挂／移
- 删除类（本技能动作闭集本无「删除」；反挂载另属 2.2.0 且仍 ask-user）
- 外写／外部安装（2.3.0 检索安装通道）

## 变更

| 日期 | 变更 |
|---|---|
| 2026-09-28 | 初版：空表白名单；agent-skills 原点 E4 实测后成文 |
| 2026-09-28 | 补 §5 表头机制（lastUpdated／refreshInterval／置信度）；空表期置信度＝高 |
