# Architecture Patterns Reference

This document assists the Agent in identifying common architectural patterns in source code.

## 1. Layered Architecture
- **Characteristics**: Divides code into layers (Presentation, Business/Service, Data Access/Repository).
- **Indicators**: 
  - Folders named `controllers/`, `services/`, `repositories/`, `models/`.
  - Dependency flow: Controller -> Service -> Repository.
- **Analysis Approach**: Check if business logic is leaking into the Controller or Repository.

## 2. Clean/Hexagonal Architecture
- **Characteristics**: Core logic sits at the center, independent of frameworks or databases.
- **Indicators**: 
  - Folders named `entities/`, `use_cases/`, `adapters/`, `ports/`.
  - Use of Interfaces/Ports for external communication.
- **Analysis Approach**: Find Interface definitions to understand boundaries between core and infrastructure.

## 3. Microservices
- **Characteristics**: System is split into small, independent services.
- **Indicators**: 
  - Multiple repositories or separate service directories (monorepo).
  - Use of Docker, Kubernetes, API Gateway.
  - Communication via HTTP/gRPC or Message Queues.
- **Analysis Approach**: Look for configuration files (e.g., `docker-compose.yml`) to understand service interactions.

## 4. Modular Monolith
- **Characteristics**: A single codebase but divided into distinct business modules.
- **Indicators**: Top-level folders represent domains (e.g., `orders/`, `users/`, `payments/`).
- **Analysis Approach**: Check for cross-module dependencies and unintended coupling.
