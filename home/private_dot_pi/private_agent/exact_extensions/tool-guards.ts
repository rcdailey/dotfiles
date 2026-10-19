import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Best-effort redirects for model-issued bash calls, not authorization. Blocking only rejects the
// call, so the prompt and cached prefix never change. Skip nested scripts and heredocs rather than
// treating their data as invocations. File-tool preference is a reminder (file-tools.ts), not a
// block: chained shell reads and transforms have too many legitimate uses to gate reliably.
function commandWords(input: string): string[][] {
  if (/<<|\$\(|`/.test(input)) return [];
  const commands: string[][] = [[]];
  let word = "";
  let open = false;
  const flush = () => {
    if (open) commands[commands.length - 1].push(word);
    word = "";
    open = false;
  };
  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === "'" || ch === '"') {
      open = true;
      const quote = ch;
      while (++i < input.length && input[i] !== quote) {
        if (quote === '"' && input[i] === "\\") i++;
        word += input[i] ?? "";
      }
      if (i === input.length) return [];
    } else if (ch === "\\") {
      const next = input[++i];
      if (next && next !== "\n") {
        word += next;
        open = true;
      }
    } else if (ch === "#" && !open) {
      while (i < input.length && input[i] !== "\n") i++;
      flush();
      commands.push([]);
    } else if (ch === "(" && open) {
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
      (/[{}]/.test(ch) && !open && (!input[i + 1] || /[\s;]/.test(input[i + 1])))
    ) {
      flush();
      commands.push([]);
    } else if (/\s/.test(ch)) {
      flush();
    } else {
      word += ch;
      open = true;
    }
  }
  flush();
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
function localInvocation(words: string[]): string[] {
  while (words.length) {
    while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[0] ?? "")) words.shift();
    const name = words[0]?.split("/").pop() ?? "";
    const wrapper = Object.hasOwn(WRAPPERS, name) ? WRAPPERS[name] : undefined;
    if (!wrapper) return words;
    words.shift();
    while (words[0]?.startsWith("-")) {
      const option = words[0];
      words.shift();
      if (option === "--") break;
      if (wrapper.flags.test(option)) continue;
      if (!wrapper.operands?.test(option.split("=")[0])) return [];
      if (!option.includes("=")) words.shift();
    }
  }
  return words;
}

interface RedirectionRule {
  command: string;
  option?: string;
  message: string;
}

const REDIRECTIONS: RedirectionRule[] = [
  {
    command: "grep",
    message: "Use 'rg' instead of 'grep' for better performance and features",
  },
  {
    command: "find",
    option: "-name",
    message: "Use 'rg --files -g pattern' instead of 'find -name'",
  },
  {
    command: "sops",
    option: "--set",
    message: "Use 'sops set' instead of 'sops --set'; consult 'sops set --help' for syntax",
  },
];

/** The violation message for a model-issued bash command, or undefined to allow it. */
export function bashViolation(command: string): string | undefined {
  for (const segment of commandWords(command)) {
    // Only the executable is redirected. git grep and remote arguments are not local grep.
    const words = localInvocation(segment);
    const name = words[0]?.split("/").pop();
    for (const rule of REDIRECTIONS) {
      if (name !== rule.command) continue;
      if (
        rule.option &&
        !words.slice(1).some((word) => word === rule.option || word.startsWith(`${rule.option}=`))
      ) {
        continue;
      }
      return rule.message;
    }
  }
}

export default function toolGuards(pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") return;
    // CustomToolCallEvent keeps toolName from narrowing the input type.
    const command = (event.input as { command?: unknown }).command;
    if (typeof command !== "string") return;
    const message = bashViolation(command);
    if (message) return { block: true, reason: `TOOL USAGE VIOLATION: ${message}` };
  });
}
