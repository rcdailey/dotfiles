---
allowed-tools: Bash
argument-hint: [context or guidance for minimal implementation]
description: TDD Green Phase - Write minimal code to make failing test pass
model: claude-3-5-sonnet-20241022
---

# TDD Green Phase: Make Test Pass

You are in the **GREEN** phase of Test-Driven Development. Your ONLY job is to write the minimal
code necessary to make the failing test pass.

## STRICT GUARDRAILS - VIOLATION IS FORBIDDEN

### ABSOLUTELY FORBIDDEN

- **NO CLEAN CODE** - Don't worry about code quality, elegance, or best practices
- **NO OPTIMIZATION** - Premature optimization is forbidden in this phase
- **NO ADDITIONAL FEATURES** - Only implement exactly what the test requires
- **NO REFACTORING** - Save improvements for the REFACTOR phase
- **NO EXTRA TESTS** - Focus solely on making the current test pass

### REQUIRED ACTIONS

1. **Write minimal code** to make the failing test pass
2. **Use simplest approach** - hard-coding, duplication, and ugly code are acceptable
3. **Run all tests** to ensure new code passes target test without breaking existing ones
4. **Stop immediately** once tests are green

## Kent Beck's Second Law of TDD

> "You may not write more production code than is sufficient to make the currently failing test
> pass"

## Green Phase Principles

- Hard-code values if it makes the test pass
- Allow duplication - removing it comes later
- Use simplest data structures
- Skip error handling unless test requires it
- Ignore edge cases not covered by current test
- Prioritize: test passes > no regressions > speed
- Defer quality improvements to REFACTOR phase

## Implementation Pattern

```txt
// Hard-code first
function add(a, b) {
  return 5; // Fine in GREEN phase
}

// Add conditionals as more tests come
function add(a, b) {
  if (a === 2 && b === 3) return 5;
  if (a === 1 && b === 4) return 5;
  // Duplication acceptable
}
```

## Process

1. Implement minimal code to satisfy failing test
2. Run target test - confirm it passes
3. Run entire test suite - ensure no regressions
4. Confirm green state

## Success Criteria

- Previously failing test now passes
- All existing tests remain passing
- Code is minimal and focused only on test requirements
- No additional functionality beyond test scope

## Avoid These Anti-Patterns

- Over-engineering the solution
- Anticipating future requirements not in tests
- Writing "proper" code instead of minimal code
- Adding error handling not required by tests
- Refactoring while implementing

## Test Feedback Loop

- Test passes - You've implemented enough
- Test fails - Need more implementation
- Other tests break - Fix regressions immediately

## Next Steps

Once tests are green:

1. Consider refactoring with `/tdd:refactor`
2. Add next test with `/tdd:red`

---

Remember: Working code is more important than beautiful code. Ugly code that passes tests is better
than beautiful code that doesn't work.
