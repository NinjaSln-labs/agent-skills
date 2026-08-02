# Design Patterns Reference

This document assists the Agent in identifying common Design Patterns.

## 1. Creational Patterns
- **Singleton**: Ensures a class has only one instance.
  - *Indicators*: Private constructor, `getInstance()` method, or a static variable holding the instance.
- **Factory Method**: Provides an interface for creating objects but lets subclasses decide which class to instantiate.
  - *Indicators*: Classes named `XYZFactory`, methods like `createProduct()`.
- **Builder**: Separates the construction of a complex object from its representation.
  - *Indicators*: Method chaining (e.g., `new UserBuilder().withName("A").withAge(20).build()`).

## 2. Structural Patterns
- **Adapter**: Allows incompatible interfaces to work together.
  - *Indicators*: A class that wraps another class and translates calls.
- **Decorator**: Dynamically adds functionality to an object.
  - *Indicators*: A class that takes an instance of the same type in its constructor and extends its behavior.
- **Facade**: Provides a simplified interface to a complex system.
  - *Indicators*: A single class that coordinates multiple underlying subsystems.

## 3. Behavioral Patterns
- **Observer**: Notifies other objects about state changes.
  - *Indicators*: `addListener()`, `subscribe()`, `notify()`.
- **Strategy**: Defines a family of algorithms and makes them interchangeable.
  - *Indicators*: Passing an object/function into an execution method (e.g., `calculate(strategy)`).
- **Dependency Injection (DI)**: Provides dependencies from the outside instead of hardcoding them.
  - *Indicators*: Constructors accepting interfaces, usage of frameworks like `Inversify`, `Spring`, or `NestJS` decorators.
