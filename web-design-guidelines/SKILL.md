---
name: web-design-guidelines
description: >-
  Review UI code files against the Vercel Labs Web Interface Guidelines, fetched
  live at runtime through any web-fetch or HTTP capability (requires network
  access to the public source, or a previously saved local copy of the
  guidelines). Outputs terse file:line findings. Use when asked to "review my
  UI", "check accessibility", "audit design", "review UX", or "check my site
  against best practices". NOT for: heuristic or usability review of interaction
  design, design-system/style/palette recommendations, WCAG tooling setup, or
  reviewing from memory — this skill only checks specified code files against the
  retrieved ruleset and declares failure when no verified copy of it can be
  obtained.
slug: web-design-guidelines
version: 1.0.1
displayName: web-design-guidelines
compatibility: >-
  Requires network access to one public raw.githubusercontent.com URL at runtime
  (any web-fetch or HTTP-request tooling applies); if retrieval fails, a
  user-provided or previously saved local copy of the same guidelines is the only
  accepted fallback.
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## How It Works

1. Fetch the latest guidelines from the source URL below (if retrieval fails, follow the Retrieval Fallback section)
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
# 直连失败/过慢时走代理（代理地址按本机环境配置，替换为实际代理地址）
curl -sL -x "http://<proxy-host>:<proxy-port>" "https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"
```

直连与代理**取速度优先**（可先各测一次延迟再选；代理端口不固定，按本机实际配置）。

## Retrieval Fallback

If the guidelines cannot be retrieved — no network, both direct and proxied requests fail, or the upstream URL returns an error (e.g. 404 after a path change):

1. Check whether a local copy of the guidelines exists (provided by the user, or saved from an earlier successful fetch). Use it only if it is the ruleset from this same source URL, and state clearly in the output that the rules come from a local copy that may be stale.
2. If no such local copy is available, STOP: tell the user the guidelines source could not be retrieved and that the review cannot be completed. Never continue from memorized or assumed rules — findings not checked against a verified copy of the guidelines are invalid.

## Usage

When a user provides a file or pattern argument:
1. Fetch guidelines from the source URL above (on failure, follow the Retrieval Fallback section above)
2. Read the specified files
3. Apply all rules from the fetched guidelines
4. Output findings using the format specified in the guidelines

If no files specified, ask the user which files to review.
