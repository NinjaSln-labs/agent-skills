# Naming Conventions Reference

Guidelines for identifying and analyzing naming standards within a project.

## 1. Variables and Functions
- **camelCase**: Commonly used in JavaScript, TypeScript, Java.
- **snake_case**: Commonly used in Python, Ruby, C++.
- **PascalCase**: Commonly used for Classes, Types, and Interfaces.

## 2. Directories and Files
- **kebab-case**: `user-service/`, `auth-controller.ts`.
- **snake_case**: `data_processor/`, `utils.py`.

## 3. Prefix/Suffix Rules
- **Interfaces**: Often start with `I` (e.g., `IUserService`) or end with `Interface`.
- **Abstract Classes**: Often start with `Base` or `Abstract`.
- **Tests**: Often end with `.spec.ts`, `.test.py`, or `Test.java`.
- **Constants**: Typically use `UPPER_SNAKE_CASE`.

## 4. Semantic Meaning
- Analyze whether function names accurately reflect their actions (e.g., `fetchData` vs `calculateTax`).
- Check for naming consistency across different modules.
