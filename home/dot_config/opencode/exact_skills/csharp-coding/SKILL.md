---
name: csharp-coding
description: Use when writing or modifying C# code
---

# C# Coding Skill

Mandatory patterns and idioms for writing modern C#. All items in this skill are requirements, not
suggestions. Use for new code; opportunistically refactor existing code when revisiting.

## Framework Detection

Before writing code, check `TargetFramework` in the project's csproj to determine the available C#
language version. If the csproj has no `TargetFramework`, look for a `Directory.Build.props` (or
other `*.props` file) that defines it; these files spread common properties across multiple
projects. Only use features whose minimum version tag (e.g., C# 12+) is satisfied by the project.
When a mandated feature is unavailable, fall back to the idiomatic alternative for that version.

## Required Language Features

- File-scoped namespaces: `namespace MyApp.Core;`
- Primary constructors (C# 12+): `class Service(IDep dep, ILogger logger)`
- Collection expressions (C# 12+): `[]`, `[item]`, `[..spread]`
  - NEVER use `new[]`, `new List<T>()`, `Array.Empty<T>()`
  - For type inference, prefer `[new T { }, new T { }]` over casts
  - Use `T[] x = [...]` only when simpler forms fail
- Records for DTOs, `init` setters
- Pattern matching: `is not null`, switch expressions, property patterns
  - Property patterns: `obj is Type { Prop: value }` over `obj is Type t && t.Prop == value`
  - Recursive/nested: `obj is Type { Outer: { Inner: value } }`
  - Extended property pattern: `obj is { Outer.Inner: value }` (C# 10)
  - Empty property pattern: `{ } name` matches non-null and binds (e.g., `is Type { Prop: { } x }`)
- Spread operator for collections (C# 12+): `[..first, ..second]`
- `field` keyword in properties (C# 14+): `public string Name { get; set => field = value ?? throw;
  } = "";`
  - NEVER use explicit backing fields when `field` suffices
- Extension blocks for extension methods and properties (C# 14+): `extension(T src) { public bool
  IsEmpty => !src.Any(); }`
  - NEVER use `static class` with `this` parameter for new extension methods
- Null-conditional assignment (C# 14+): `obj?.Prop = value;` over null checks wrapping assignment
- Lambda modifiers without types (C# 14+): `(text, out result) => int.TryParse(text, out result)`
  - NEVER add redundant parameter types when modifiers alone suffice

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

- Configure naming policy, converters, and style via `JsonSerializerOptions` (or source-generated
  `JsonSerializerContext`) so conventions apply uniformly
- Check for existing options configuration before creating new instances
- Reserve per-property attributes (`[JsonPropertyName]`, etc.) for exceptions to the convention

### UsedImplicitly Attribute

Mark runtime-used members (deserialization, reflection, DI):

- `[UsedImplicitly]` - type instantiated implicitly (DI, empty marker records)
- `[UsedImplicitly(ImplicitUseKindFlags.Assign)]` - properties set via deserialization
- `[UsedImplicitly(..., ImplicitUseTargetFlags.WithMembers)]` - applies to type AND all members
- Common for DTOs: `[UsedImplicitly(ImplicitUseKindFlags.Assign,
  ImplicitUseTargetFlags.WithMembers)]`

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
- Add explicit `return;` or `continue;` if needed to separate main logic from local function defs

## Design Principles

### Quality Gates

- Zero warnings/analysis issues - treat warnings as errors
- All code must pass static analysis before commit

### Abstraction

- Prefer polymorphism over enums when modeling behavior or extensibility
- Propose enum vs polymorphism tradeoffs for discussion rather than defaulting to enums
- Every abstraction must justify its existence with concrete current needs

### Dependency Injection

- MUST use DI for all dependencies; NEVER manually `new` service objects in production code
- Concrete implementations get injected; tests can substitute
- Search existing registrations before adding new ones

## Comment Guidelines

Comments must earn their place by reducing cognitive load. When to comment:

- LINQ chains (3+ operations): Brief comment stating transformation goal
- Conditional blocks with non-obvious purpose: One-line comment (e.g., `// Explicit: user
  specified`)
- Private methods: Block comment if name + parameters don't make purpose self-evident
- Early returns/continues: Include reason if not obvious from context
- Complex algorithms: Comment explaining approach at top, not line-by-line
- Null-suppression operator (`!`): Every use MUST have an inline comment explaining why null is
  impossible at that point (e.g., `// non-null: validated above`, `// non-null: dict always contains
  key after init`). The comment documents the runtime guarantee so reviewers can verify it and
  future maintainers can detect if the invariant breaks.
- General: Any code where a reader would pause and wonder "why?" or "what's happening here?"

NEVER:

- XML doc comments (unless public API library)
- Commented-out code
- Restating what code literally does

## Tooling

### Formatting

- CSharpier is the ONLY formatting tool
- NEVER use `dotnet format` or other formatters
- Run pre-commit hooks on all changed files

### dotnet CLI

- Use dotnet CLI for: adding/removing packages, adding projects to solution
- Central package management via `Directory.Packages.props` - specify versions there, not in csproj
- Avoid `--no-build` or `--no-restore` flags; `dotnet test` handles restore + build automatically
- Quiet verbosity for build/test: `dotnet build -v q`, `dotnet test -v q`
- For verbose debugging, pipe to file: `dotnet test -v d 2>&1 > /tmp/test.log` then search with `rg`

### Project Structure

- SLNX format preferred over traditional SLN
- One Autofac/DI module per library to keep registration modular
- Dotnet tools configured in `.config/dotnet-tools.json`
- Keep source files flat in their project directory; create subdirectories only when file count
  makes navigation difficult
