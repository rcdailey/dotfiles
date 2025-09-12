---
allowed-tools: Bash
argument-hint: [refactoring goals or specific improvements to target]
description: TDD Refactor Phase - Improve code quality while keeping tests green
---

# TDD Refactor Phase: Improve Code Quality

You are in the **REFACTOR** phase of Test-Driven Development. Your job is to improve code quality,
design, and maintainability while keeping all tests green.

## STRICT GUARDRAILS - VIOLATION IS FORBIDDEN

### ABSOLUTELY FORBIDDEN

- **NO BEHAVIOR CHANGES** - External behavior must remain identical
- **NO TEST MODIFICATIONS** - Tests define the contract, don't change them
- **NO FUNCTIONALITY ADDITIONS** - Only improve existing code structure
- **NO BREAKING EXISTING TESTS** - All tests must remain green throughout
- **NO LARGE REFACTORINGS** - Make small, incremental improvements

### REQUIRED ACTIONS

1. **Run tests before any changes** to establish green baseline
2. **Make small, incremental improvements** to code structure and quality
3. **Run tests after each change** to ensure nothing breaks
4. **Apply design principles** (SOLID, DRY) to improve maintainability
5. **Follow existing codebase conventions** and patterns

## Kent Beck's Third Law of TDD

> "You may not refactor code unless you have passing tests"

## Refactoring Principles

- Run tests frequently after every small change
- Make one change at a time
- Revert immediately if tests break
- Keep changes small

### Target Improvements (based on `$ARGUMENTS`)

1. Remove duplication (DRY)
2. Extract methods/functions for clarity
3. Improve naming for readability
4. Apply SOLID principles
5. Follow codebase conventions

## SOLID Principles Application

- **SRP**: Extract methods that do only one thing
- **OCP**: Use polymorphism instead of conditionals
- **LSP**: Ensure derived classes can replace base classes
- **ISP**: Split large interfaces into focused ones
- **DIP**: Depend on abstractions, not concretions

## Common Refactoring Patterns

### Extract Method

```txt
// Before: Long method
function processOrder(order) {
  // validation, pricing, inventory, shipping logic
}

// After: Extracted methods
function processOrder(order) {
  validateOrder(order);
  const price = calculatePrice(order);
  updateInventory(order);
  scheduleShipping(order);
}
```

### Remove Duplication & Extract Constants

```txt
// Before: Duplicated + magic numbers
function calculateTaxForUS(amount) { return amount * 0.08; }
function calculateTaxForCA(amount) { return amount * 0.12; }
if (user.age >= 21) { /* logic */ }

// After: Parameterized + constants
function calculateTax(amount, rate) { return amount * rate; }
const LEGAL_DRINKING_AGE = 21;
if (user.age >= LEGAL_DRINKING_AGE) { /* logic */ }
```

## Codebase Convention Analysis

Before refactoring, analyze existing code for:

- Naming conventions (camelCase, snake_case, etc.)
- Error handling patterns
- Dependency management approaches
- Common design patterns in use
- Module organization principles

## Incremental Process

1. Identify code smell or improvement opportunity
2. Run tests to ensure green state
3. Make smallest possible improvement
4. Run tests to verify nothing broke
5. Commit the change (if using version control)
6. Repeat with next small improvement

### Example Session

```txt
1. Tests green → Extract magic number → Tests green
2. Tests green → Rename unclear variable → Tests green
3. Tests green → Extract long method → Tests green
4. Tests green → Remove duplication → Tests green
```

## Code Smell Detection

### Watch for

- Long methods → Extract smaller methods
- Large classes → Split into cohesive classes
- Duplicate code → Extract common functionality
- Unclear names → Use descriptive names
- Feature envy → Move methods to appropriate classes
- Data clumps → Group related data into objects

## Testing During Refactoring

- Run tests before each change
- Run tests after each change
- Use full test suite, not subset

### When Tests Break

1. Stop immediately
2. Analyze the failure
3. Revert the change
4. Try smaller change

## Success Criteria

- All tests remain green throughout refactoring
- Code quality improvements achieved per `$ARGUMENTS`
- External behavior unchanged
- Codebase conventions followed
- Design principles applied appropriately

## Next Steps

After refactoring:

1. Confirm all tests green
2. Review improvements
3. Continue TDD cycle with `/tdd:red` for next behavior

---

Remember: Refactoring improves existing code while preserving behavior. Small, safe steps with
continuous test feedback are key.
