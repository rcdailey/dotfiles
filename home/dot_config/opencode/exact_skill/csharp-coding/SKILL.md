---
name: csharp-coding
description: C# 14 and .NET 10 coding patterns, idioms, and conventions
---

# C# Coding Skill

Patterns and idioms for writing modern C# code.

<overview>

This skill covers C# 14 language features, .NET 10 conventions, and idiomatic C# development.
Load this skill before writing or modifying C# code.

</overview>

<context name="language-features">

## Required Language Features

- File-scoped namespaces: `namespace MyApp.Core;`
- Primary constructors: `class Service(IDep dep, ILogger logger)`
- Collection expressions (MANDATORY): `[]`, `[item]`, `[..spread]`
  - NEVER use `new[]`, `new List<T>()`, `Array.Empty<T>()`
  - For type inference, prefer `[new T { }, new T { }]` over casts
  - Use `T[] x = [...]` only when simpler forms fail
- Records for DTOs, `init` setters
- Pattern matching: `is not null`, switch expressions
- Spread operator for collections: `[..first, ..second]`

## C# 14 Features (.NET 10)

- `field` keyword: `public string Name { get; set => field = value ?? throw; } = "";`
- Extension blocks: `extension(T src) { public bool IsEmpty => !src.Any(); }` (properties + statics)
- Null-conditional assignment: `obj?.Prop = value;` (RHS evaluated only if obj not null)
- Lambda modifiers without types: `(text, out result) => int.TryParse(text, out result)`

Migration: Use new syntax for new code; opportunistically refactor existing code when revisiting.

</context>

<context name="idioms">

## Required Idioms

### Visibility

- Use `internal` for implementation classes (CLI apps, service implementations)
- Use `public` only for genuine external APIs
- Concrete classes implementing public interfaces should be `internal`

### Data Modeling

- Records for data models
- Favor immutability where reasonable
- Use immutable collections: `IReadOnlyCollection`, `IReadOnlyDictionary`

### JSON Serialization

- System.Text.Json: Use `JsonSerializerOptions` for convention/style settings applied uniformly
- Reserve attributes (`[JsonPropertyName]`, etc.) for special cases only
- Check for existing options configuration before creating new instances

### UsedImplicitly Attribute

Mark runtime-used members (deserialization, reflection, DI):

- `[UsedImplicitly]` - type instantiated implicitly (DI, empty marker records)
- `[UsedImplicitly(ImplicitUseKindFlags.Assign)]` - properties set via deserialization
- `[UsedImplicitly(..., ImplicitUseTargetFlags.WithMembers)]` - applies to type AND all members
- Common for DTOs: `[UsedImplicitly(ImplicitUseKindFlags.Assign, ImplicitUseTargetFlags.WithMembers)]`

### Warning Suppression

- NEVER use `#pragma warning disable`
- Use `[SuppressMessage]` with `Justification` on class/method level
- Prefer class-level when multiple members need same suppression

### LINQ

- LINQ method chaining over loops
- LINQ method syntax only; NEVER use query syntax (from/where/select keywords)

### Method Calls

- Named arguments for boolean literals: `new Options(SendInfo: false, SendEmpty: true)`
- Named arguments for consecutive same-type parameters to clarify intent

### Async

- `ValueTask` for hot paths
- `CancellationToken` everywhere (use `ct` for variable name)

### Interfaces

- Avoid interface pollution: not every service class must have an interface
- Add interfaces when justified (testability, more than one implementation)

### Local Functions

- Local functions go after `return`/`continue` statements
- Add explicit `return;` or `continue;` if needed to separate main logic from local function definitions

</context>
