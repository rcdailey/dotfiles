import { describe, expect, test } from "bun:test";
import { findCodeBlocks } from "./blocks.ts";

describe("findCodeBlocks", () => {
  test("returns tagged and untagged blocks in document order", () => {
    const markdown = "Intro\n\n```ts\nconst a = 1\n```\n\ntext\n\n```\nplain\n```\n";
    expect(findCodeBlocks(markdown)).toEqual([
      { lang: "ts", code: "const a = 1", fenced: "```ts\nconst a = 1\n```" },
      { lang: "", code: "plain", fenced: "```\nplain\n```" },
    ]);
  });

  test("uses the first info-string word as the language", () => {
    expect(findCodeBlocks("```bash title=x\nls\n```")[0]?.lang).toBe("bash");
  });

  test("accepts tilde fences and keeps shorter inner fences as code", () => {
    const markdown = "~~~~md\n```js\nx\n```\n~~~~";
    expect(findCodeBlocks(markdown)).toEqual([
      { lang: "md", code: "```js\nx\n```", fenced: "~~~~md\n```js\nx\n```\n~~~~" },
    ]);
  });

  test("strips list-item indentation from nested blocks", () => {
    const markdown = "1. Run:\n\n   ```sh\n   make\n     indented\n   ```\n- ```txt\n  a\n  ```";
    expect(findCodeBlocks(markdown).map((block) => block.code)).toEqual(["make\n  indented", "a"]);
  });

  test("strips blockquote markers from nested blocks", () => {
    const markdown = "> ```py\n> print(1)\n> ```";
    expect(findCodeBlocks(markdown)).toEqual([
      { lang: "py", code: "print(1)", fenced: "```py\nprint(1)\n```" },
    ]);
  });

  test("closes a quoted block where its blockquote ends", () => {
    const markdown = "> ```py\n> print(1)\nafter";
    expect(findCodeBlocks(markdown).map((block) => block.code)).toEqual(["print(1)"]);
  });

  test("excludes an unclosed final fence", () => {
    expect(findCodeBlocks("```ts\nconst partial =")).toEqual([]);
  });

  test("keeps an empty block", () => {
    expect(findCodeBlocks("```json\n```")).toEqual([
      { lang: "json", code: "", fenced: "```json\n```" },
    ]);
  });

  test("ignores backtick fences whose info string contains a backtick", () => {
    expect(findCodeBlocks("```a`b\nx\n```")).toEqual([]);
  });
});
