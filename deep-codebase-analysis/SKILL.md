---
name: deep-codebase-analysis
description: >-
  Deep codebase analysis: read and analyze an entire software project's source to
  understand architecture, communication, design patterns, and business flows. Use when
  the user asks to analyze the overall structure of a whole codebase (exploring a new
  system, understanding architecture before maintenance, or scoping a refactor). NOT for:
  single-file edits, auditing one skill's SKILL.md, or reviewing a small diff — those
  belong to code-review / skill-description-audit.
slug: deep-codebase-analysis
version: 1.1.1
displayName: deep-codebase-analysis
---

# Deep Codebase Analysis

## Overview

This skill enables the Agent to perform a comprehensive analysis of a software project, from high-level architecture to implementation details, helping developers quickly grasp complex systems.

## Core Capabilities

### 1. Overall Architecture Analysis
- Identify key components and organizational models (layered, microservices, modular, clean architecture, etc.).
- Map data flows and inter-module dependencies (dependency mapping).

### 2. Component Communication
- Recognize interaction mechanisms: APIs (REST, GraphQL, gRPC), Message Queues (RabbitMQ, Kafka), Event Bus, or direct function calls.
- Understand how components share memory or state.

### 3. Design Patterns
- Detect common patterns: Singleton, Factory, Observer, Dependency Injection, Strategy, etc.
- Evaluate how these patterns are applied and their consistency across the codebase.

### 4. Rules and Conventions (Coding Conventions)
- Grasp naming conventions, directory structure, and project-specific best practices.
- Check compliance with established coding standards.

### 5. Business Logic Flow
- Trace a request's journey from UI to Database and back.
- Analyze complex business rules embedded in the code.

### 6. State and Data Management
- Understand how data is stored, retrieved, and synchronized via Databases, Cache (Redis), Sessions, etc.
- Analyze schemas and entity relationships.

### 7. Error Handling and Logging
- Analyze exception handling strategies, logging, and system monitoring mechanisms.

## Workflow

1. **Scanning and Indexing**: Use search and analysis tools to build a relationship model between files.
2. **Static Analysis**: Trace function calls, inheritance, and imports to identify main entry points.
3. **Visualization**: (If supported) Create dependency diagrams or flowcharts.
4. **Contextual Inference**: Combine information from documentation, comments, and commit history to understand design intent.
5. **Verification**: Formulate hypotheses about the system and verify them by deep-diving into the source code.

## Usage Guide

When you need to analyze a codebase, start by asking the Agent:
- "Analyze the overall architecture of this project."
- "How does the processing flow work from when a user clicks 'Pay' to when it's saved in the DB?"
- "What are the main design patterns used in this project?"

## Quick Start (helper script)

Precondition: a checkout at `/path/to/repo`.

```bash
python3 scripts/analyze_structure.py /path/to/repo --depth 2
```

Output excerpt (actual script behavior — prints a two-level directory tree):

```
--- Project Structure: /path/to/repo ---
repo/
    src/
        api/
        models/
    tests/
    package.json
```

The script is a preliminary aid only; the analysis itself (architecture, patterns, flows) is done by the agent reading the source per the Workflow section. Defaults: `--depth 2`; `--exclude` already skips `node_modules`, `vendor`, `.git`, `__pycache__`, `.DS_Store`.

## Worked Example

Ask: "Analyze the overall architecture of this project."

Observable flow: run the helper script (Quick Start) → scan/index → trace entry points → produce a report naming the architecture model, key components, communication mechanisms, and a data-flow narrative, each backed by cited source paths. Excerpt of an expected finding:

```
Architecture: modular monolith
- Entry points: src/main.ts, src/worker.ts
- Communication: REST (Express) internally; Kafka for async jobs
- Persistence: PostgreSQL via Prisma; Redis for sessions
```

## Failure Exits

- Path does not exist or is not a directory: the script prints only the `--- Project Structure: ... ---` header with no tree under it — treat that as a wrong-path signal, tell the user the path was empty, and ask for the correct one. Do not "analyze" nothing.
- Empty or skeleton repo (fewer than ~10 source files): say so and analyze directly — the full workflow adds no value there.
- Monorepo: run the helper once per package, then analyze cross-package boundaries separately instead of treating the monorepo as one flat tree.
- Documentation contradicts the code: trust the code and report the contradiction as a finding — do not average the two.

## NOT for / Anti-patterns (observable)

- NOT for reviewing a small diff or a single file — "review my last commit" belongs to `code-review`.
- NOT for security auditing — misconfigurations and secrets belong to `config-scan` / `secrets-scan`.
- Anti-pattern: summarizing the README and calling it analysis — every claim must cite a source path.
- Anti-pattern: reading the whole tree file-by-file before forming hypotheses — hypothesize early, then verify by deep-diving (Workflow step 5).
- Anti-pattern: naming patterns without evidence ("uses Factory") — name the class/file where the pattern lives.

## Wrong → Right (FAQ)

| Wrong | Right |
|---|---|
| Running the helper on a nonexistent path and continuing | Header with no tree = wrong path; stop and ask |
| One flat analysis of a monorepo | Per-package structure + a separate boundary analysis |
| Claims sourced from docs/comments only | Verify in code; report doc/code contradictions |
| Reporting every design pattern found | Report the load-bearing ones and their consistency |

## 中文速览（Quick Guide）

- **做什么**：通读整个代码库，产出架构模型、组件通信、设计模式与业务流程的分析报告，每个结论都引用源码路径佐证。
- **何时用**：接手新系统、维护或重构前需要整体理解代码库结构时（小 diff / 单文件评审不适用）。
- **核心步骤**：①扫描建索引 ②静态分析追入口与调用链 ③（可选）画依赖图 ④结合文档与提交史推断设计意图 ⑤提出假设并回源码验证。
- **国内可达性**：主流程离线可完成（本地源码 + 自带脚本），无境外服务依赖。

## Resources

### scripts/
- [analyze_structure.py](scripts/analyze_structure.py): A helper script to visualize project directory structure for preliminary architectural analysis. Supports excluding unnecessary directories via the `--exclude` parameter.

### references/
- [architecture_patterns.md](references/architecture_patterns.md): Reference for common architectural models and their indicators.
- [naming_conventions.md](references/naming_conventions.md): Common source code naming standards.
- [design_patterns.md](references/design_patterns.md): Catalog of common design patterns and how to identify them in code.
