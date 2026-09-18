import { expect, test } from "bun:test";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { parse } from "jsonc-parser";

const path = join(import.meta.dir, "../../home/dot_config/opencode/cli.json");

test("keeps the migrated terminal settings", async () => {
  const errors: unknown[] = [];
  const config = parse(await readFile(path, "utf8"), errors, { allowTrailingComma: true });
  expect(errors).toEqual([]);
  expect(config.$schema).toBe("https://opencode.ai/v2/cli.json");
  expect(config.attention.enabled).toBeUndefined();
  expect(config.attention.volume).toBe(0.4);
  expect(config.diffs.view).toBe("unified");
  expect(config.keybinds["session.parent"]).toBe("alt+up");
  expect(config.keybinds["session.child.first"]).toBe("alt+down");
  expect(config.keybinds["session.tab.next"]).toBe("ctrl+tab");
  expect(config.keybinds["session.tab.previous"]).toBe("ctrl+shift+tab");
  expect(config.keybinds["input.buffer.home"]).toBe("none");
  expect(config.keybinds["input.buffer.end"]).toBe("none");
});
