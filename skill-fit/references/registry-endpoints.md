# 渠道与端点表（registry / 安装 / 反馈）

> skill-fit 的「占用查重 / 安装坐标 / 反馈投递」数据源。**非 `catalog.yaml` 副本**——硬约束 7 只禁复制 catalog；本表只列渠道端点与命令。
> 单一来源：SKILL.md 正文不复制端点/命令，改本表即可（防双源漂移）。
> lastUpdated: 2026-09-19 · refreshInterval: 长期（渠道或端点变更时修订）· 置信度: 高（均为官方公开端点）

## 一、占用查重 + 安装坐标

| 渠道 | 查重端点 | 安装命令 / 坐标 | 置信度 | 备注 |
|------|----------|------------------|--------|------|
| SkillHub | `GET https://api.skillhub.cn/api/v1/skills/{slug}?namespace=<handle>` | SkillHub 平台安装 | 高 | `<handle>` 见 `catalog.yaml` 的 `owner.skillhub_handle` |
| skills.sh | `GET https://skills.sh/api/search?q=<name>` | `npx skills add NinjaSln-labs/agent-skills` | 高 | 整仓分发 |
| 本地真源链入 | 不适用（本地文件系统） | `ln -sfn <真源仓>/<name> <目标>/.agents/skills/<name>` | 高 | 本机常态；消费侧 `~/.agents/skills/<name>` 为符号链接 |

## 二、未收录 / 其它渠道（**不假设 SkillHub**）

技能可能由本表未收录的渠道安装（其它市场 / 企业内网 registry / 私有分发 / 手工拷贝）。届时：

- **占用查重**：标注「**占用未核验**」，**不臆断**、**不臆造端点**；可提示用户把该渠道补进本表。
- **安装坐标**：按**实际安装来源**给（本地真源 / 实装渠道），勿默认 SkillHub。
- **数据源定位**：仍走 SKILL.md「数据源定位」（按文件系统实际存在判定 `catalog.yaml`/`retired.txt`/`scripts/`）；单技能拷贝等无兄弟件的安装 → 降级为 frontmatter 推断并声明。

## 三、反馈投递目标

| 目标 | 端点 / 命令 | 置信度 | 备注 |
|------|-------------|--------|------|
| 上游公开仓（默认） | `gh issue create --repo NinjaSln-labs/agent-skills --title "[skill-fit] <项目类型> · 反馈" --body-file <报告路径> --label enhancement` | 高 | 优先；有 `gh` 时用 |
| 无 `gh` | `https://github.com/NinjaSln-labs/agent-skills/issues/new?title=<编码标题>&body=<编码正文>` | 高 | 打印预填 URL，由用户手动提交 |

- **默认投递到上游** `NinjaSln-labs/agent-skills`；若本技能经**其它分发渠道**安装且其上游不同，按该渠道上游调整，或在报告中注明。
- 投递**前**必须展示脱敏报告给用户确认（硬约束 6）。
