# Contributing

Thanks for your interest in improving **pixel-perfect (Visual Regression)** — a
Claude Code skill for automated screenshot-comparison testing with Playwright.

## How to Contribute

### Report a Bug
Open an [issue](../../issues) with:
- What you expected to happen
- What actually happened (e.g. a false-positive diff, or a real change that went undetected)
- The Playwright version and OS/browser you ran against
- A minimal before/after example if you can share one

### Suggest an Improvement
Open an [issue](../../issues) describing:
- The problem or limitation you hit
- Your proposed solution
- An example use case

### Submit a Pull Request
1. Fork the repo
2. Create a branch (`git checkout -b improve-baseline-handling`)
3. Edit `SKILL.md` (the main skill file at repo root); keep supporting material in `references/`
4. Test locally (see below)
5. Submit a PR with a clear description of what changed and why

### Testing Your Changes
```bash
# Clone your fork into the Claude Code skills directory
git clone https://github.com/YOUR_USERNAME/claude-skill-visual-regression.git ~/.claude/skills/pixel-perfect

# Start a new Claude Code conversation and trigger the skill, e.g.:
# "Run visual regression on <page> and compare against the baseline"

# Verify the skill loads, captures a baseline, and flags/ignores diffs as expected
```

### Skill Authoring Guidelines
- Keep `SKILL.md` concise — every line should earn its place
- Maintain the YAML frontmatter (`name`, `description`, `license`, `metadata`) and the
  `TRIGGER` / `DO NOT TRIGGER` boundaries so the skill activates only when appropriate
- Prefer stable comparisons: mask dynamic regions, wait for fonts/animations to settle,
  and keep viewport/device settings explicit to avoid flaky diffs

## Code of Conduct
Be respectful and constructive. This is a small tool built to save people time —
let's keep it welcoming.
