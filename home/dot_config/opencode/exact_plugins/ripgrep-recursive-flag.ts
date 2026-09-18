import type { Plugin } from "@opencode/plugin";

interface Word {
  value: string;
  start: number;
  end: number;
}

// Keep the same best-effort shell boundary as tool-guards.ts.
function commandWords(input: string): Word[][] {
  if (/<<|\$\(|`/.test(input)) return [];
  const commands: Word[][] = [[]];
  let value = "";
  let start = -1;
  const begin = (index: number) => {
    if (start === -1) start = index;
  };
  const flush = (end: number) => {
    if (start !== -1) commands[commands.length - 1].push({ value, start, end });
    value = "";
    start = -1;
  };

  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === "'" || ch === '"') {
      begin(i);
      const quote = ch;
      while (++i < input.length && input[i] !== quote) {
        if (quote === '"' && input[i] === "\\") i++;
        value += input[i] ?? "";
      }
      if (i === input.length) return [];
      continue;
    }
    if (ch === "\\") {
      begin(i);
      const next = input[++i];
      if (next && next !== "\n") value += next;
      continue;
    }
    if (ch === "#" && start === -1) {
      while (i < input.length && input[i] !== "\n") i++;
      flush(i);
      commands.push([]);
      continue;
    }
    if (
      /[|&;\n()]/.test(ch) ||
      (/[{}]/.test(ch) && start === -1 && (!input[i + 1] || /[\s;]/.test(input[i + 1])))
    ) {
      flush(i);
      commands.push([]);
      continue;
    }
    if (/\s/.test(ch)) {
      flush(i);
      continue;
    }
    begin(i);
    value += ch;
  }
  flush(input.length);
  return commands.filter((words) => words.length > 0);
}

function rewriteCommand(input: string): string {
  const edits: Array<{ start: number; end: number; value: string }> = [];
  for (const words of commandWords(input)) {
    let commandIndex = 0;
    while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[commandIndex]?.value ?? "")) {
      commandIndex++;
    }
    if (words[commandIndex]?.value.split("/").pop() !== "rg") continue;

    for (const word of words.slice(commandIndex + 1)) {
      if (word.value === "--") break;
      const match = /^-([A-Za-z]*r[A-Za-z]*)$/.exec(word.value);
      if (!match) continue;
      const option = `-${match[1].replaceAll("r", "")}`;
      let end = word.end;
      if (option === "-") {
        while (end < input.length && /[ \t]/.test(input[end])) end++;
      }
      edits.push({ start: word.start, end, value: option === "-" ? "" : option });
    }
  }

  return edits
    .reverse()
    .reduce(
      (command, edit) => command.slice(0, edit.start) + edit.value + command.slice(edit.end),
      input,
    );
}

/** Removes grep-style recursive short flags from ordinary local ripgrep commands. */
export const RipgrepRecursiveFlag = {
  id: "local.ripgrep-recursive-flag",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "shell") return;
      if (!event.input || typeof event.input !== "object") return;
      const command = Reflect.get(event.input, "command");
      if (typeof command !== "string") return;
      Reflect.set(event.input, "command", rewriteCommand(command));
    });
  },
} satisfies Plugin.Plugin;

export default RipgrepRecursiveFlag;
