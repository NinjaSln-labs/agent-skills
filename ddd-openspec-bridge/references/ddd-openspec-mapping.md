# DDD → OpenSpec Mapping（执行标准）

> 本文件是 `ddd-openspec-bridge` 的包内执行标准，替代上游 monorepo 的 `docs/ddd-openspec-mapping.md`。

lastUpdated: 2026-08-03
refreshInterval: 180
confidence: high

## §2.1 映射方向

| OpenSpec 工件 | 来源 DDD 工件 | 规则 |
|---------------|---------------|------|
| Requirement | `ddd-domain-interactions` 命令 / 领域服务 | 一条可独立验证的业务能力；Scenario ≤ 5；不跨聚合根 |
| Scenario | `ddd-aggregates` 行为与不变量 | Given/When/Then；P0 不变量必须有 Scenario |
| 领域事件 | 交互定义中的事件 | 写在 Scenario 的 Then/And（副作用），不单独成 Requirement |
| proposal Why | `ddd-scope` 问题陈述 | 保持问题导向 |
| What Changes / Capabilities | `ddd-subdomains` + `ddd-contexts` | Core 全量 Scenario 化；Generic 可引用既有规范 |
| design.md 集成 | `ddd-context-map` + 交互机制 | ACL、Outbox、幂等键 |

## 业务规则优先

Scenario **只**描述业务规则与不变量，禁止渗入数据库、HTTP、ORM、缓存等技术细节。技术落点写在 `design.md`。

## 附录 A：事务与事件约束

- 一次事务仅修改**一个**聚合
- 跨聚合协作走领域事件 + Outbox
- 消费端必须幂等（幂等键）
- `specs/` 按限界上下文分目录，禁止扁平 `specs/domain-model/`

## §5 最小示例骨架（用户注册）

```text
Requirement: 用户可完成注册
  Scenario: 有效邮箱首次注册成功
    Given 邮箱未被占用
    When 提交注册
    Then 创建用户聚合
    And 发布 UserRegistered 事件
  Scenario: 重复邮箱被拒绝
    Given 邮箱已存在
    When 提交注册
    Then 拒绝并提示邮箱已占用
```
