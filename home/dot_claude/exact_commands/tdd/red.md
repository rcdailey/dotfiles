---
allowed-tools: Bash
argument-hint: [test description or behavior to implement]
description: TDD Red Phase - Write a single failing test for specified behavior
model: claude-3-5-sonnet-20241022
---

# TDD Red Phase: Write Failing Test

You are in the **RED** phase of Test-Driven Development. Your ONLY job is to write a single failing
test.

## STRICT GUARDRAILS - VIOLATION IS FORBIDDEN

### ABSOLUTELY FORBIDDEN

- **NO PRODUCTION CODE** - Do not write any implementation code whatsoever
- **NO PASSING TESTS** - The test MUST fail initially
- **NO MULTIPLE TESTS** - Write exactly ONE test at a time
- **NO SETUP CODE** - Only write the minimal test structure needed
- **NO IMPLEMENTATION HINTS** - Do not suggest or write any solution code

### REQUIRED ACTIONS

1. **Write ONE failing test** that describes the desired behavior from `$ARGUMENTS`
2. **Use appropriate testing framework** based on project language/setup
3. **Run the test** and verify it fails with a clear, meaningful error message
4. **Stop immediately** after confirming the test fails as expected

## Kent Beck's First Law of TDD

> "You may not write production code until you have written a failing unit test"

## Test Writing Principles

- One test validates one specific behavior
- Test name clearly describes expected behavior
- Focus on WHAT the code should do, not HOW
- Auto-detect testing framework (Jest, pytest, JUnit, etc.)
- Use Arrange-Act-Assert structure

## Example Pattern

```txt
test('should [expected behavior] when [condition]', () => {
  expect(functionToTest(input)).toBe(expectedOutput);
});
```

## Process

1. Write the test describing behavior in `$ARGUMENTS`
2. Run the test and confirm failure
3. Validate clear error message

## Success Criteria

- One test written that captures desired behavior
- Test fails when executed
- Failure reason is clear
- No production code written

## Avoid These Anti-Patterns

- Testing implementation details instead of behavior
- Writing multiple tests at once
- Making tests pass immediately
- Adding production code to make tests compile

## Next Steps

After test fails as expected, use `/tdd:green` to implement minimal code.

---

Remember: In TDD, a failing test is SUCCESS. It proves you're testing the right behavior.
