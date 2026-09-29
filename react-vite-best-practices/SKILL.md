---
name: react-vite-best-practices
description: >-
  React and Vite performance optimization guidelines. Use when writing, reviewing, or
  optimizing React components built with Vite. Triggers on tasks involving Vite
  configuration, build optimization, code splitting, lazy loading, HMR, bundle size,
  asset handling (images/fonts/SVG), environment variables, or React performance.
slug: react-vite-best-practices
version: 1.1.1
displayName: react-vite-best-practices
---

# React + Vite Best Practices

Comprehensive performance optimization guide for React applications built with Vite. Contains 23 rules across 6 categories for build optimization, code splitting, development performance, asset handling, environment configuration, and bundle analysis.

## Metadata

- **Framework:** React + Vite
- **Rule Count:** 23 rules across 6 categories
- **License:** MIT

## When to Apply

Reference these guidelines when:
- Configuring Vite for React projects
- Implementing code splitting and lazy loading
- Optimizing build output and bundle size
- Setting up development environment and HMR
- Handling images, fonts, SVGs, and static assets
- Managing environment variables across environments
- Analyzing bundle size and dependencies

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Build Optimization | CRITICAL | `build-` |
| 2 | Code Splitting | CRITICAL | `split-` |
| 3 | Development | HIGH | `dev-` |
| 4 | Asset Handling | HIGH | `asset-` |
| 5 | Environment Config | MEDIUM | `env-` |
| 6 | Bundle Analysis | MEDIUM | `bundle-` |

## Quick Reference

### 1. Build Optimization (CRITICAL)

- `build-manual-chunks` - Configure manual chunks for vendor separation
- `build-minification` - Minification with OXC (default) or Terser
- `build-target-modern` - Target modern browsers (baseline-widely-available)
- `build-sourcemaps` - Configure sourcemaps per environment
- `build-tree-shaking` - Ensure proper tree shaking with ESM
- `build-compression` - Gzip and Brotli compression
- `build-asset-hashing` - Content-based hashing for cache busting

### 2. Code Splitting (CRITICAL)

- `split-route-lazy` - Route-based splitting with React.lazy()
- `split-suspense-boundaries` - Strategic Suspense boundary placement
- `split-dynamic-imports` - Dynamic import() for heavy components
- `split-component-lazy` - Lazy load non-critical components
- `split-prefetch-hints` - Prefetch chunks on hover/idle/viewport

### 3. Development (HIGH)

- `dev-dependency-prebundling` - Configure optimizeDeps for faster starts
- `dev-fast-refresh` - React Fast Refresh patterns
- `dev-hmr-config` - HMR server configuration

### 4. Asset Handling (HIGH)

- `asset-image-optimization` - Image optimization and lazy loading
- `asset-svg-components` - SVGs as React components with SVGR
- `asset-fonts` - Web font loading strategy
- `asset-public-dir` - Public directory vs JavaScript imports

### 5. Environment Config (MEDIUM)

- `env-vite-prefix` - VITE_ prefix for client variables
- `env-modes` - Mode-specific environment files
- `env-sensitive-data` - Never expose secrets in client code

### 6. Bundle Analysis (MEDIUM)

- `bundle-visualizer` - Analyze bundles with rollup-plugin-visualizer

## Essential Configurations

### Recommended vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  build: {
    target: 'baseline-widely-available',
    sourcemap: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },

  optimizeDeps: {
    include: ['react', 'react-dom'],
  },

  server: {
    port: 3000,
    hmr: {
      overlay: true,
    },
  },
})
```

### Route-Based Code Splitting

```typescript
import { lazy, Suspense } from 'react'

const Home = lazy(() => import('./pages/Home'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      {/* Routes here */}
    </Suspense>
  )
}
```

### Environment Variables

```typescript
// src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/build-manual-chunks.md
rules/split-route-lazy.md
rules/env-vite-prefix.md
```

## References

- [Vite Documentation](https://vite.dev)
- [React Documentation](https://react.dev)
- [Rollup Documentation](https://rollupjs.org)

## Full Compiled Document

For the complete guide with all rules expanded: `REFERENCE.md`

## How to Invoke (Example Phrasings)

Name the category or rule prefix in your request; the skill reads the matching `rules/*.md` files:

- "Review my `vite.config.ts` for build optimization" → build rules
- "My initial page load is slow — help me split routes" → `split-route-lazy`, `split-dynamic-imports`
- "Images are killing my LCP" → asset rules
- "Where should I put secrets — `.env` or code?" → env rules
- "Bundle is 2 MB, help me find what's in it" → `bundle-visualizer`

## Example Session (Shortest Path)

**Precondition:** a React + Vite repo with `vite.config.ts` present.
**Invocation:** "Apply build-optimization rules to my vite.config.ts."
**Outcome:** `build-manual-chunks` + `build-target-modern` applied to the config (vendor chunk split, modern browser target), quoting the Incorrect/Correct snippets from the cited rule files, with a completion check: `npm run build` succeeds and output chunk sizes are reported.

## When NOT to Apply

- Non-Vite build tooling (webpack, CRA, Rspack) or non-React frameworks — rule file paths and APIs are Vite-specific.
- Runtime performance profiling (React DevTools, `performance.mark`) — this skill covers build-time and asset-level optimization, not runtime profiling methodology.
- General linting/formatting (ESLint, Prettier) or backend/API performance — out of scope.

## Failure Exits

| Situation | Observable signal | Exit |
| --- | --- | --- |
| Rule file missing | `rules/<name>.md` referenced by the task does not exist on disk (read fails, e.g. `rules/split-route-lazy.md: No such file`) | Say which rule files were unavailable; apply the Quick Reference summary for those prefixes only — do not invent rule content or cite snippets that were never read. |
| Dependencies not installed | `npm run build` fails with `vite: not found` / `sh: vite: command not found`, or imports of `react`/`vite` fail to resolve | Ask the user (or run) `npm install` first; state that build-based verification could not run until then — do not report optimization results from a project that cannot build. |
| `npm run build` exits non-zero after changes | Compiler/resolution errors in the build output, exit code != 0 | Treat it as a finding: the applied change is unverified. Identify whether the config change caused it (revert the specific edit if so), fix or report, and re-run until the build passes — never declare success with a red build. |

## FAQ

**"The rules mention 20–50% improvements — is that guaranteed?"** No. Impact descriptions are directional, from typical cases; verify on your project with `npx vite build` output or `bundle-visualizer` before/after.

**"No automated checker?"** Correct — documentation-only skill. Apply the CRITICAL `build-` and `split-` rules manually first.

**"Which rules first for a small project?"** `split-route-lazy`, `build-manual-chunks`, `env-sensitive-data` — highest impact per minute spent.
---

## 中文速览（Quick Guide）

- **做什么**：为 React + Vite 项目提供 23 条性能优化规则，覆盖构建优化／代码分割／开发体验／静态资源／环境变量／包分析六类。
- **何时用**：配置 Vite、做代码分割与懒加载、压包体、处理图片字体 SVG 与环境变量时。
- **核心步骤**：按规则前缀定位并**先读仓内 `rules/*.md` 本地副本**（含 Incorrect/Correct 片段）→ 按摘要套用到配置与代码 → `npm run build` 跑通并报告 chunk 体积后才算完成。
- **国内可达性边界**：正文与 `rules/` 全部是本地文档，读规则无需网络；vite.dev／react.dev／rollupjs.org 外链仅为官方文档延伸阅读，不访问不影响使用；`npm install` 依赖下载可走 npmmirror 等镜像源。

