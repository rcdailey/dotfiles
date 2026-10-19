import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Removes grep-style recursive short flags from model-issued rg calls: rg recurses by default and
// `-r` is `--replace`, so `rg -rn foo src/` silently treats `n` as replacement text. Rewriting runs
// the intended search instead of failing the call. Command-level redirects (grep, find -name,
// sops --set, gh api without --method) are deny rules in pi-permission-system/config.json.
// Best-effort, not authorization: skip nested scripts and heredocs rather than treating their
// data as invocations.

interface Word {
  value: string;
  start: number;
  end: number;
}

function commandWords(input: string): Word[][] {
  if (/<<|\$\(|`/.test(input)) return [];
  const commands: Word[][] = [[]];
  let word = "";
  let start = -1;
  const open = () => start !== -1;
  const begin = (index: number) => {
    if (start === -1) start = index;
  };
  const flush = (end: number) => {
    if (open()) commands[commands.length - 1].push({ value: word, start, end });
    word = "";
    start = -1;
  };
  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === "'" || ch === '"') {
      begin(i);
      const quote = ch;
      while (++i < input.length && input[i] !== quote) {
        if (quote === '"' && input[i] === "\\") i++;
        word += input[i] ?? "";
      }
      if (i === input.length) return [];
    } else if (ch === "\\") {
      begin(i);
      const next = input[++i];
      if (next && next !== "\n") word += next;
    } else if (ch === "#" && !open()) {
      while (i < input.length && input[i] !== "\n") i++;
      flush(i);
      commands.push([]);
    } else if (ch === "(" && open()) {
      // Keep attached zsh glob qualifiers in their argument, not as command groups.
      word += ch;
      let depth = 1;
      while (i + 1 < input.length && depth) {
        const next = input[++i];
        word += next;
        if (next === "(") depth++;
        if (next === ")") depth--;
      }
    } else if (
      /[|&;\n()]/.test(ch) ||
      (/[{}]/.test(ch) && !open() && (!input[i + 1] || /[\s;]/.test(input[i + 1])))
    ) {
      flush(i);
      commands.push([]);
    } else if (/\s/.test(ch)) {
      flush(i);
    } else {
      begin(i);
      word += ch;
    }
  }
  flush(input.length);
  return commands.filter((words) => words.length > 0);
}

const WRAPPERS: Record<string, { flags: RegExp; operands?: RegExp }> = {
  sudo: {
    flags: /^(?:-[nEHSkKb]|--non-interactive|--preserve-env|--set-home|--stdin|--background)$/,
    operands: /^(?:-[ughpCTRD]|--user|--group|--host|--prompt|--close-from|--chroot|--chdir)$/,
  },
  env: {
    flags: /^(?:-i|--ignore-environment)$/,
    operands: /^(?:-[uC]|--unset|--chdir)$/,
  },
  command: { flags: /^-p$/ },
};

// Unknown wrapper options can change execution semantics (e.g. env -S or command -v).
function localInvocation(words: Word[]): Word[] {
  while (words.length) {
    while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[0]?.value ?? "")) words.shift();
    const name = words[0]?.value.split("/").pop() ?? "";
    const wrapper = Object.hasOwn(WRAPPERS, name) ? WRAPPERS[name] : undefined;
    if (!wrapper) return words;
    words.shift();
    while (words[0]?.value.startsWith("-")) {
      const option = words[0].value;
      words.shift();
      if (option === "--") break;
      if (wrapper.flags.test(option)) continue;
      if (!wrapper.operands?.test(option.split("=")[0])) return [];
      if (!option.includes("=")) words.shift();
    }
  }
  return words;
}

/** The command with `r` removed from every rg short-flag cluster (`-rl` -> `-l`, `-r` -> ''). */
export function stripRipgrepRecursiveFlag(input: string): string {
  const edits: Word[] = [];
  for (const segment of commandWords(input)) {
    const words = localInvocation(segment);
    if (words[0]?.value.split("/").pop() !== "rg") continue;
    for (const word of words.slice(1)) {
      if (word.value === "--") break;
      const match = /^-([A-Za-z]*r[A-Za-z]*)$/.exec(word.value);
      if (!match) continue;
      const flags = match[1].replaceAll("r", "");
      let end = word.end;
      if (!flags) while (/[ \t]/.test(input[end] ?? "")) end++;
      edits.push({ start: word.start, end, value: flags && `-${flags}` });
    }
  }
  return edits.reduceRight(
    (command, edit) => command.slice(0, edit.start) + edit.value + command.slice(edit.end),
    input,
  );
}

export default function toolGuards(pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") return;
    // CustomToolCallEvent keeps toolName from narrowing the input type.
    const input = event.input as { command?: unknown };
    if (typeof input.command === "string") input.command = stripRipgrepRecursiveFlag(input.command);
  });
}
