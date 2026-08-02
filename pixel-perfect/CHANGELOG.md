# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Automated visual-regression workflow using Playwright's `toHaveScreenshot()` —
  capture a baseline, then surface pixel-level diffs after code changes.
- Full-setup workflow that scaffolds `package.json` and installs the Chromium
  runtime when no Playwright config is present, so the skill works from a clean repo.
- `CONTRIBUTING.md` with bug-report, improvement and pull-request guidelines.

_First documented changelog entry; earlier changes predate this file._
