# 弃用公告模板集

> 用途：把「弃用四件套」（**文档标注 · 运行时告警 · 迁移路径 · 时间线**）从原则变成可直接套用的文本。
> 配套：`version-management` 正文「废弃政策」；HTTP 场景的头部定义见 RFC 9745（`Deprecation`）与 RFC 8594（`Sunset`）。

---

## 0. 先定时间线（其余模板都引用它）

弃用必须有**两个日期**，且窗口按稳定级别给足：

| 稳定级别 | 弃用公告 → 移除的最短窗口（参考 Kubernetes 政策） |
|---|---|
| 稳定 / GA | 当前主版本内**不移除**；仅公告弃用 |
| Beta | ≥ 3 个次版本或 9 个月（取更长） |
| Alpha | 可随时移除，无需事先公告 |

```
版本计划（示例）
  v2.14.0  公告弃用 <feature>          ← 同时发 MINOR（SemVer 第 7 条）
  v2.15.0  运行时告警持续；文档已标注
  v2.16.0  最后支持版本（仍可用）
  v3.0.0   移除 <feature>              ← MAJOR 才允许移除
```

> 要点：**弃用发 MINOR，移除只能换 MAJOR**；两者之间至少隔一个 MINOR。

---

## 1. 文档标注模板（README / API 参考 / 类型注释）

```markdown
> **Deprecated since v2.14.0** — will be removed in v3.0.0.
>
> Use [`<newApi>`](#anchor) instead. Migration guide: [docs/migration/<feature>.md](...).
> Reason: <一句话说明为什么弃用>.
```

代码内（行内注释 / 文档字符串）：

```
// Deprecated since v2.14.0; removed in v3.0.0. Use newFn() instead.
// Migration: docs/migration/old-fn.md
```

**不要**只写 `@deprecated` 而不给替代与版本——读者需要的是**换什么**和**什么时候必须换**。

---

## 2. 运行时告警模板

```
DeprecationWarning: api.oldFn() is deprecated since v2.14.0 and will be removed in v3.0.0.
  Use api.newFn() instead. See https://<docs>/migration/old-fn
```

要求：

- 告警里出现**三个要素**：当前版本、移除版本、替代品/迁移链接。
- 告警**幂等且不刷屏**（同类告警每次进程/会话只报一次），否则会被用户全局静音，等于没告警。
- 告警必须能被**自动化捕获**（可 grep 的固定前缀，如 `DeprecationWarning:`），便于调用方在 CI 里当失败条件。

---

## 3. HTTP 弃用信号模板（RFC 9745 + RFC 8594）

```http
HTTP/1.1 200 OK
Deprecation: @1749427200
Sunset: Wed, 31 Dec 2025 23:59:59 GMT
Link: <https://api.example.com/docs/migration/old-endpoint>; rel="deprecation"; type="text/html"
Link: <https://api.example.com/v2/new-endpoint>; rel="successor-version"
Warning: 299 - "This endpoint is deprecated and will be sunset on 2025-12-31. See Link rel=deprecation."
```

- `Deprecation`（RFC 9745）：**弃用生效时间**（结构化字段，示例为时间戳形式）。
- `Sunset`（RFC 8594）：**关停时间**（HTTP-date）。
- `Link rel="deprecation"` 指向说明；`rel="successor-version"` 指向替代端点。
- `Warning`（299）为兼容旧客户端的冗余提示，可保留。

> 调用方应把 `Sunset` 当**硬截止**做自动巡检（到期前的告警/阻断）。

---

## 4. CHANGELOG 模板（Keep a Changelog）

公告弃用的那一版（`Deprecated` 组）：

```markdown
## [2.14.0] - 2025-06-10

### Deprecated
- `api.oldFn()` — 将于 **3.0.0** 移除，替换为 `api.newFn()`（迁移指南：docs/migration/old-fn.md）。自本版本起调用会产生 `DeprecationWarning`。

### Added
- `api.newFn()`，覆盖 `oldFn()` 的全部能力并支持 <新特性>。
```

真正移除的那一版（`Removed` 组）：

```markdown
## [3.0.0] - 2025-12-31

### Removed
- **BREAKING**：移除 `api.oldFn()`（2.14.0 起弃用）。迁移指南：docs/migration/old-fn.md。

### Changed
- …（其余 MAJOR 变更）
```

撤回有问题的版本（损坏版本，要响亮）：

```markdown
## [2.13.2] - 2025-06-01 [YANKED]
- 该版本在 <场景> 下会 <故障>，已由 2.13.3 取代。请勿使用。
```

> 规则：弃用与移除**各自出现在对应的版本节**，不要合并成一句「移除 X（早就弃用了）」——读者需要能顺着 CHANGELOG 找到弃用起点。

---

## 5. 迁移指南骨架

```markdown
# Migrating from <old> to <new>

**Deadline: v3.0.0（计划 2025-12-31）** · 弃用公告：v2.14.0

## 你会遇到什么
- v2.14.0 起：调用 <old> 产生弃用告警（不影响功能）
- v3.0.0 起：<old> 被移除，调用将 <报错/返回 X>

## 改法（before → after）
```diff
- result = oldFn(input)
+ result = newFn(toNewInput(input))
```

## 行为差异
| 场景 | 旧行为 | 新行为 | 需要做什么 |
|---|---|---|---|
| <边界输入> | <…> | <…> | <…> |

## 无法立即迁移？
- 临时开关：<flag/兼容层>（将在 v3.1.0 一并移除）
- 联系我们：<渠道>
```

---

## 6. 自检清单（发弃用版本前）

- [ ] 弃用**发的是 MINOR**（不是 PATCH），且 CHANGELOG `Deprecated` 组已列
- [ ] 文档已标注：**当前版本 · 移除版本 · 替代品 · 迁移链接**
- [ ] 运行时告警已加：含三要素、幂等不刷屏、可被自动化捕获
- [ ] 迁移路径可执行：指南 + before/after 示例 + 行为差异表
- [ ] 时间线已公布，且窗口符合稳定级别（GA 主版本内不移除 / Beta ≥3 次版本或 9 个月 / Alpha 无要求）
- [ ] HTTP/API 场景：`Deprecation` + `Sunset` + `Link` 头已下发，调用方可自动巡检
- [ ] **没有**朝更不稳定的替代品做弃用（GA 不得弃用给 beta）
- [ ] 移除动作排在**下一个 MAJOR**，且已同步进 CHANGELOG `Removed` 组
