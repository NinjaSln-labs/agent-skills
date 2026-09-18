# 跨周期完成记录（cycles）

> 归档口径：被后续周期取代的「最近完成」类内容与已交付周期，从 HANDOFF §1/§2 迁到此处。
> 保留编号锚点，不删号、不重排。

## 2026-09-17 · 技能库优化批次

- `problem-dive` + `problem-resolution-flow` 合并为 `problem-handling`（单源：诊断→分级→处置→收尾）；旧名登记 `renames.yaml`。
- 新增 `catalog.yaml`（技能适配维度单源）与 `skill-fit`（技能适配管家，只读 v1，仅用户 `/skill:skill-fit`）。
- 新增 `version-management`（通用版本管理，不依赖 VCS）+ 三份 references（生态对照 / 弃用公告模板 / 调研与出处）。
- 新增 `scripts/skill-name-check.{sh,ps1}`（技能重名预检，namespace 优先判定），写入「新增技能」流程第 0 步。
- 退役 `core-rules`；硬约束「凭据不落明文」迁入 7 个 agent CLI 的用户级记忆文件。
- 交接规范瘦身：`project-handoff` / `project-intake` 定为 5 节 ≤1K tokens + 环境指纹 + `.agents/session.md` 收敛。
