---
name: deep-codebase-analysis
description: >-
  Deep codebase analysis: read and analyze an entire software project's source to
  understand architecture, communication, design patterns, and business flows. Use when
  the user asks to analyze the overall structure of a whole codebase (exploring a new
  system, understanding architecture before maintenance, or scoping a refactor). NOT for:
  single-file edits, auditing one skill's SKILL.md, or reviewing a small diff — those
  belong to code-review / skill-description-audit.
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

## Resources

### scripts/
- [analyze_structure.py](scripts/analyze_structure.py): A helper script to visualize project directory structure for preliminary architectural analysis. Supports excluding unnecessary directories via the `--exclude` parameter.

### references/
- [architecture_patterns.md](references/architecture_patterns.md): Reference for common architectural models and their indicators.
- [naming_conventions.md](references/naming_conventions.md): Common source code naming standards.
- [design_patterns.md](references/design_patterns.md): Catalog of common design patterns and how to identify them in code.
