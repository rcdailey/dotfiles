---
description: Generate comprehensive behavior-focused tests for the specified code area
argument-hint: <code-path-or-description>
---

# Generate Behavior-Focused Tests

Write comprehensive behavior-focused tests for the specified code area: $ARGUMENTS

## Process

1. **Scan and Analyze**: Examine the target code (class, module, function, or project area) to understand its public interface, functionality, and expected behaviors
2. **Detect Test Framework**: Identify the existing test framework from current test files in the project
3. **Generate Tests**: Create comprehensive behavior-focused tests following these principles

## Test Writing Guidelines

### Focus on Behavior, Not Implementation
- Test input-output relationships and expected behavior
- Test the public interface, not internal workings
- Use descriptive test names that explain the behavior being tested
- Cover various scenarios, including edge cases and error conditions
- Avoid testing private methods or internal state directly
- Write independent tests that don't rely on state from other tests

### Test Structure
- Group related tests into appropriate test classes/describe blocks
- Write individual test methods for each specific behavior
- Use setup/teardown methods when necessary
- Follow the conventions of the detected testing framework

### Coverage Areas
- **Main functionality**: Core features and expected behaviors
- **Edge cases**: Boundary conditions and unusual inputs
- **Error conditions**: Invalid inputs and failure scenarios
- **Integration points**: How the code interacts with dependencies
- **State management**: How the code handles state changes over time

## Good Example
```javascript
describe('ShoppingCart', () => {
  test('add_item_increases_cart_size', () => {
    const cart = new ShoppingCart();
    const initialSize = cart.items.length;
    cart.addItem('Apple');
    expect(cart.items.length).toBe(initialSize + 1);
  });
});
```

## Avoid Implementation-Specific Tests
```javascript
// Don't write tests like this:
test('add_item_uses_array_data_structure', () => {
  const cart = new ShoppingCart();
  cart.addItem('Apple');
  expect(Array.isArray(cart.items)).toBe(true);
});
```

## Output Requirements

- Generate only the test code using appropriate syntax and conventions
- Ensure comprehensive coverage of the main functionality
- Include meaningful test descriptions that explain the expected behavior
- Follow the existing project's testing patterns and naming conventions
- Do not include additional explanations or comments outside the test code
