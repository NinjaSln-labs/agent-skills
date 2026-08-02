---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## How It Works

1. Fetch the latest guidelines from the source URL below
2. Read the specified files (or prompt user for files/pattern)
3. Check against all rules in the fetched guidelines
4. Output findings in the terse `file:line` format

## Guidelines Source

Fetch fresh guidelines before each review:

```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

Use WebFetch to retrieve the latest rules. The fetched content contains all the rules and output format instructions.

If the environment has no WebFetch tool, fall back to curl against the same URL and review with the same rules:

```bash
# 直连优先
curl -sL "https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"
# 直连失败/过慢时走代理（代理地址按本机环境配置；如 macOS 系统代理 127.0.0.1:6696）
curl -sL -x "http://127.0.0.1:6696" "https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"
```

直连与代理**取速度优先**（可先各测一次延迟再选；代理端口不固定，按本机实际配置）。

## Usage

When a user provides a file or pattern argument:
1. Fetch guidelines from the source URL above
2. Read the specified files
3. Apply all rules from the fetched guidelines
4. Output findings using the format specified in the guidelines

If no files specified, ask the user which files to review.
