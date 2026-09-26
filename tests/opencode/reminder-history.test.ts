import { expect, test } from "bun:test";
import {
  decodeHistory,
  extendPrefix,
} from "../../home/dot_config/opencode/exact_plugins/lib/reminder-history.ts";

test("the persisted contract retains text and deliberate omissions after serialization", () => {
  const first = extendPrefix("", { role: "user", content: "One" });
  const second = extendPrefix(first, { role: "user", content: "Two" });
  const journal = {
    version: 1 as const,
    entries: { [first]: "Original guidance", [second]: null },
  };
  expect(decodeHistory(JSON.parse(JSON.stringify(journal)))).toEqual(journal);
  expect(decodeHistory(undefined)).toEqual({ version: 1, entries: {} });
});

test("invalid or unknown history versions are rejected without modifying storage", () => {
  for (const value of [
    null,
    [],
    {},
    { version: 2, entries: {} },
    { version: 1, entries: { x: 1 } },
  ]) {
    const before = structuredClone(value);
    expect(() => decodeHistory(value)).toThrow("Invalid reminder history");
    expect(value).toEqual(before);
  }
});

test("prefix identity ignores object key order, not message content or ordering", () => {
  const first = extendPrefix("", { role: "user", content: "One" });
  expect(extendPrefix("", { content: "One", role: "user" })).toBe(first);
  expect(extendPrefix("", { role: "user", content: "Two" })).not.toBe(first);
  expect(extendPrefix(first, { role: "user", content: "One" })).not.toBe(first);
});
