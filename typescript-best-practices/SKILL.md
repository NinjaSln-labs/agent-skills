---
name: typescript-best-practices
description: >-
  Guide AI agents through TypeScript coding best practices including type safety, error
  handling, code organization, and architecture patterns. This skill should be used when
  generating TypeScript code, reviewing TypeScript files, creating new TypeScript modules,
  refactoring JavaScript to TypeScript, or when the user asks about TypeScript patterns,
  types, or coding standards. Keywords: typescript, types, coding standards, best
  practices, type safety, generics, architecture, refactoring. Use when scaffolding a
  TypeScript module, generating TypeScript types from JSON data, or analyzing TypeScript
  code for quality issues.
slug: typescript-best-practices
version: 1.1.1
displayName: typescript-best-practices
---

# TypeScript Best Practices

Guide AI agents in writing high-quality TypeScript code. This skill provides coding standards, architecture patterns, and tools for analysis and scaffolding.

## When to Use This Skill

Use this skill when:
- Generating new TypeScript code
- Reviewing TypeScript files for quality issues
- Creating new modules, services, or components
- Refactoring JavaScript to TypeScript
- Answering questions about TypeScript patterns or types
- Designing APIs or interfaces

Do NOT use this skill when:
- Working with pure JavaScript (no TypeScript)
- Debugging runtime errors (use debugging tools)
- Framework-specific patterns (React, Vue, etc. - use framework skills)

## Getting Started

Say one of these to invoke it (anything you paste with the invocation counts as given context):

- `Use typescript-best-practices to review ./src for type-safety issues and suggest fixes.`
- `Scaffold a user-service module with tests following this skill's standards.`
- `Generate TypeScript types from this JSON response` (+ paste the JSON).

Typical flow: 1) run `scripts/analyze.ts` on the target path for a baseline, 2) apply the Core Principles and Quick Reference below (deep dives in `references/`), 3) use `scripts/scaffold-module.ts` for new modules and re-run the analyzer to confirm.

## Core Principles

### 1. Type Safety First

Maximize compile-time error detection:

```typescript
// Prefer unknown over any for unknown types
function processInput(data: unknown): string {
  if (typeof data === "string") return data;
  if (typeof data === "number") return String(data);
  throw new Error("Unsupported type");
}

// Explicit return types for public APIs
export function calculateTotal(items: ReadonlyArray<Item>): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Use const assertions for literal types
const CONFIG = {
  mode: "production",
  version: 1,
} as const;
```

### 2. Immutability by Default

Prevent accidental mutations:

```typescript
// Use readonly for object properties
interface User {
  readonly id: string;
  readonly email: string;
  name: string; // Only mutable if intentional
}

// Use ReadonlyArray for collections
function processItems(items: ReadonlyArray<Item>): ReadonlyArray<Result> {
  return items.map(transform);
}

// Prefer spreading over mutation
function updateUser(user: User, name: string): User {
  return { ...user, name };
}
```

### 3. Error Handling with Types

Use the type system for error handling:

```typescript
// Result type for recoverable errors
type Result<T, E = Error> =
  | { success: true; value: T }
  | { success: false; error: E };

// Typed error classes
class ValidationError extends Error {
  constructor(
    message: string,
    readonly field: string,
    readonly code: string
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

// Function with Result return type
function parseConfig(input: string): Result<Config, ValidationError> {
  try {
    const data = JSON.parse(input);
    if (!isValidConfig(data)) {
      return {
        success: false,
        error: new ValidationError("Invalid config", "root", "INVALID_FORMAT"),
      };
    }
    return { success: true, value: data };
  } catch {
    return {
      success: false,
      error: new ValidationError("Parse failed", "root", "PARSE_ERROR"),
    };
  }
}
```

### 4. Code Organization

Structure code for maintainability:

```typescript
// One concept per file
// user.ts - User type and related utilities
export interface User {
  readonly id: string;
  readonly email: string;
  readonly createdAt: Date;
}

export function createUser(email: string): User {
  return {
    id: crypto.randomUUID(),
    email,
    createdAt: new Date(),
  };
}

// Explicit exports (no barrel file wildcards)
// index.ts
export { User, createUser } from "./user.ts";
export { validateEmail } from "./validation.ts";
```

## Quick Reference

| Category | Prefer | Avoid |
|----------|--------|-------|
| Unknown types | `unknown` | `any` |
| Collections | `ReadonlyArray<T>` | `T[]` for inputs |
| Objects | `Readonly<T>` | Mutable by default |
| Null checks | Optional chaining `?.` | `!= null` |
| Type narrowing | Type guards | `as` assertions |
| Return types | Explicit on exports | Inferred on exports |
| Enums | String literal unions | Numeric enums |
| Imports | Named imports | Default imports |
| Errors | Result types | Throwing for flow control |
| Loops | `for...of`, `.map()` | `for...in` on arrays |

### Script Exit Codes and Failure Exits

- `analyze.ts` exits `1` when **critical issues were found** (that is a finding, not a crash), when the path does not exist, or when no TypeScript files were found at the path — check the message to tell which.
- `generate-types.ts` exits `1` on invalid JSON input or write failures; fix the JSON (or the output path) and re-run.
- `scaffold-module.ts` exits `1` when the target directory already exists (pick another `--name`/`--path`) or `--type` is invalid (allowed: `service`, `util`, `component`, `hook`).
- No Deno installed: the checks cannot run — fall back to manual review against the Quick Reference and Common Anti-Patterns tables instead of skipping the review.
- Scripts are read-only helpers (except scaffold/generate output); never let a clean analyzer run override a manual review finding.

## FAQ

| Wrong turn | Better path |
|------------|-------------|
| "Analyzer passed, so the code is fine" | The analyzer catches a subset (mostly `any`/assertion issues); type design and architecture still need the Core Principles applied |
| Reaching for `any` "just this once" for an untyped API boundary | Type it `unknown` and narrow with a type guard; see `references/type-system/type-guards.md` |
| Fixing a reported type error with `as SomeType` | `as` silences the compiler without making the code correct — narrow or restructure instead |
| Migrating JS → TS by renaming `.js` to `.ts` and fixing errors as they come | Start from the strict tsconfig presets in `assets/tsconfig-presets/`, then fix compile errors deliberately |
| "Which reference file do I read?" | Error handling → `references/patterns/error-handling.md`; async → `async-patterns.md`; exports/DI → `module-patterns.md`; narrowing → `type-guards.md` |

## Code Generation Guidelines

When generating TypeScript code, follow these patterns:

### Module Structure

```typescript
/**
 * Module description
 * @module module-name
 */

// === Types ===
export interface ModuleOptions {
  readonly setting: string;
}

export interface ModuleResult {
  readonly data: unknown;
}

// === Constants ===
const DEFAULT_OPTIONS: ModuleOptions = {
  setting: "default",
};

// === Implementation ===
export function processData(
  input: unknown,
  options: Partial<ModuleOptions> = {}
): ModuleResult {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  // Implementation
  return { data: input };
}
```

### Function Design

```typescript
// Pure functions preferred
function transform(input: Input): Output {
  // No side effects, same input = same output
  return { ...input, processed: true };
}

// Explicit parameter types
function fetchUser(id: string, options?: FetchOptions): Promise<User> {
  // Implementation
}

// Use function overloads for complex signatures
function parse(input: string): ParsedData;
function parse(input: Buffer): ParsedData;
function parse(input: string | Buffer): ParsedData {
  // Implementation
}
```

### Interface Design

```typescript
// Prefer interfaces for object shapes
interface UserData {
  readonly id: string;
  readonly email: string;
}

// Use type for unions and intersections
type UserRole = "admin" | "user" | "guest";
type AdminUser = UserData & { readonly role: "admin" };

// Document with JSDoc
/**
 * Configuration for the API client
 * @property baseUrl - The base URL for API requests
 * @property timeout - Request timeout in milliseconds
 */
interface ApiConfig {
  readonly baseUrl: string;
  readonly timeout?: number;
}
```

## Common Anti-Patterns

Avoid these patterns when generating code:

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `any` type | Disables type checking | Use `unknown` and narrow |
| `as` assertions | Runtime errors | Use type guards |
| Non-null `!` | Null pointer errors | Optional chaining `?.` |
| Mutable params | Unexpected mutations | `Readonly<T>` |
| Magic strings | Typos, no autocomplete | String literal types |
| God classes | Hard to test/maintain | Single responsibility |
| Circular deps | Build/runtime issues | Dependency inversion |
| Index signatures | Lose type info | Explicit properties |

See `references/anti-patterns/common-mistakes.md` for detailed examples.

## Scripts Reference

### analyze.ts

Analyze TypeScript code for quality issues:

```bash
deno run --allow-read scripts/analyze.ts <path> [options]

Options:
  --strict        Enable all checks
  --json          Output JSON for programmatic use
  --fix-hints     Show suggested fixes

Examples:
  # Analyze a file
  deno run --allow-read scripts/analyze.ts ./src/utils.ts

  # Analyze directory with strict mode
  deno run --allow-read scripts/analyze.ts ./src --strict

  # JSON output for CI
  deno run --allow-read scripts/analyze.ts ./src --json
```

### generate-types.ts

Generate TypeScript types from JSON data:

```bash
deno run --allow-read --allow-write scripts/generate-types.ts <input> [options]

Options:
  --name <name>   Root type name (default: inferred)
  --output <path> Output file path
  --readonly      Generate readonly types
  --interface     Use interface instead of type

Examples:
  # Generate from JSON file
  deno run --allow-read scripts/generate-types.ts ./data.json --name Config

  # Generate readonly interface
  deno run --allow-read --allow-write scripts/generate-types.ts ./api-response.json \
    --interface --readonly --output ./types/api.ts
```

### scaffold-module.ts

Create properly structured TypeScript modules:

```bash
deno run --allow-read --allow-write scripts/scaffold-module.ts [options]

Options:
  --name <name>   Module name (required)
  --path <path>   Target directory (default: ./src)
  --type <type>   Type: service, util, component, hook
  --with-tests    Include test file

Examples:
  # Create a utility module
  deno run --allow-read --allow-write scripts/scaffold-module.ts \
    --name "string-utils" --type util

  # Create a service with tests
  deno run --allow-read --allow-write scripts/scaffold-module.ts \
    --name "user-service" --type service --with-tests
```

## 中文速览（Quick Guide）

**这个技能做什么**：指导 AI 生成与审查高质量 TypeScript 代码——先跑分析脚本拿基线，再按类型安全、不可变、Result 型错误处理等核心原则修正，最后用脚手架脚本落地新模块并复检。

**何时用**：生成/审查 TypeScript 代码、新建模块、JS 迁移 TS，或被问到 TS 模式与类型问题时（纯 JS、运行时报错调试、框架专属模式不适用）。

**核心步骤**：
1. 对目标路径运行 `analyze.ts` 取质量基线；
2. 对照 Core Principles 与 Quick Reference 逐条修正（`any`→`unknown`+收窄、显式返回类型、readonly 集合）；
3. 新模块用 `scaffold-module.ts` 生成骨架并复跑分析器确认；
4. JS→TS 迁移从 `assets/tsconfig-presets/` 严格预设起步，而非改后缀后逐错硬修。

**国内可达性边界**：三个脚本依赖本机 Deno 运行时；deno.land 安装源不可达时按正文既有出口降级为对照 Quick Reference 与反模式表手工审查（结论不变）。references/、assets/ 均为仓内本地文件，主流程无其他境外服务依赖。

## Additional Resources

### Type System Deep Dives
- `references/type-system/advanced-types.md` - Generics, conditional types, mapped types
- `references/type-system/type-guards.md` - Type narrowing techniques
- `references/type-system/utility-types.md` - Built-in utility types

### Pattern Guides
- `references/patterns/error-handling.md` - Result types, typed errors
- `references/patterns/async-patterns.md` - Async/await best practices
- `references/patterns/functional-patterns.md` - Immutability, composition
- `references/patterns/module-patterns.md` - Exports, dependency injection

### Architecture
- `references/architecture/project-structure.md` - Directory organization
- `references/architecture/api-design.md` - Interface design, versioning

### Templates
- `assets/templates/module-template.ts.md` - Module starter template
- `assets/templates/service-template.ts.md` - Service class template
- `assets/tsconfig-presets/strict.json` - Maximum strictness config
- `assets/tsconfig-presets/recommended.json` - Balanced defaults
