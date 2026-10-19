import { statSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Best-effort redirects for model-issued bash calls, not authorization. Blocking only rejects the
// call, so the prompt and cached prefix never change. File-tool gates block only when the parse is
// unambiguous; syntax the parser does not model passes through.

interface Segment {
  words: string[];
  /** stdout feeds a pipe, so the output is processed rather than read. */
  piped: boolean;
  /** stdout goes to a file or descriptor, so the command is copying, not reading. */
  redirected: boolean;
}

// Nested scripts and process substitution hide invocations; heredoc bodies are data, not words.
const UNMODELED = /<<|\$\(|`|[<>]\(/;

function segments(input: string): Segment[] {
  if (UNMODELED.test(input)) return [];
  const result: Segment[] = [];
  let current: Segment = { words: [], piped: false, redirected: false };
  let word = "";
  let open = false;
  let target = false;
  const flush = () => {
    if (open) {
      if (target) target = false;
      else current.words.push(word);
    }
    word = "";
    open = false;
  };
  const end = (piped = false) => {
    flush();
    target = false;
    current.piped = piped;
    if (current.words.length) result.push(current);
    current = { words: [], piped: false, redirected: false };
  };
  const redirect = (output: boolean, fd: string) => {
    // Descriptor duplication (2>&1) and stderr redirection leave stdout on the terminal.
    if (output && (fd === "" || fd === "1" || fd === "&")) current.redirected = true;
    target = true;
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
      end();
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
    } else if (ch === ">" || ch === "<") {
      const fd = open && /^\d+$/.test(word) ? word : "";
      if (fd) {
        word = "";
        open = false;
      } else flush();
      if (ch === ">" && input[i + 1] === "&" && /\d/.test(input[i + 2] ?? "")) {
        // >&N duplicates a descriptor; the digits are not a file target.
        i += 2;
        while (/\d/.test(input[i + 1] ?? "")) i++;
        if (fd === "" || fd === "1") current.redirected = true;
        continue;
      }
      while (/[>|&]/.test(input[i + 1] ?? "")) i++;
      redirect(ch === ">", fd);
    } else if (ch === "&") {
      if (input[i + 1] === ">") {
        flush();
        i++;
        while (input[i + 1] === ">") i++;
        redirect(true, "&");
      } else {
        if (input[i + 1] === "&") i++;
        end();
      }
    } else if (ch === "|") {
      if (input[i + 1] === "|") {
        i++;
        end();
      } else {
        if (input[i + 1] === "&") i++;
        end(true);
      }
    } else if (
      /[;\n()]/.test(ch) ||
      (/[{}]/.test(ch) && !open && (!input[i + 1] || /[\s;]/.test(input[i + 1])))
    ) {
      end();
    } else if (/\s/.test(ch)) {
      flush();
    } else {
      word += ch;
      open = true;
    }
  }
  end();
  return result;
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

/** Strip assignments and known wrappers. Unknown wrapper options can change execution semantics. */
function localInvocation(input: string[]): { words: string[]; elevated: boolean } {
  const words = [...input];
  let elevated = false;
  while (words.length) {
    while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[0] ?? "")) words.shift();
    const name = words[0]?.split("/").pop() ?? "";
    const wrapper = Object.hasOwn(WRAPPERS, name) ? WRAPPERS[name] : undefined;
    if (!wrapper) return { words, elevated };
    if (name === "sudo") elevated = true;
    words.shift();
    while (words[0]?.startsWith("-")) {
      const option = words[0];
      words.shift();
      if (option === "--") break;
      if (wrapper.flags.test(option)) continue;
      if (!wrapper.operands?.test(option.split("=")[0])) return { words: [], elevated };
      if (!option.includes("=")) words.shift();
    }
  }
  return { words, elevated };
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

const READ_MESSAGE = "Use the read tool to view files (offset/limit for line ranges)";
const EDIT_MESSAGE = "Use the edit tool for in-place file changes";
const WRITE_MESSAGE = "Use the write tool to create files instead of heredoc redirection";

/** Option words; everything after `--` is an operand. Options in `withArg` consume the next word. */
function split(args: string[], withArg: RegExp): { options: string[]; operands: string[] } {
  const options: string[] = [];
  const operands: string[] = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--") {
      operands.push(...args.slice(i + 1));
      break;
    }
    if (arg.startsWith("-") && arg !== "-") {
      options.push(arg);
      if (withArg.test(arg)) options.push(args[++i] ?? "");
    } else operands.push(arg);
  }
  return { options, operands };
}

const CAT_PLAIN = /^(?:-[nbsu]+|--number|--number-nonblank|--squeeze-blank)$/;
const HEAD_TAIL_ARG = /^(?:-[nc]|--lines|--bytes|-s|--sleep-interval|--pid|--max-unchanged-stats)$/;
const HEAD_TAIL_RAW = /^(?:-c|--bytes|-f|-F|--follow|--retry|--pid)/;
const SED_ARG = /^(?:-[ef]|--expression|--file|-l|--line-length)$/;
// Line-address print scripts only (`5p`, `1,80p`, `10,$p;20p`); anything else transforms output.
const SED_PRINT = /^\s*(?:(?:\d+|\$)(?:\s*,\s*(?:\d+|\$))?\s*p\s*;?\s*)+$/;

/** Operands a direct file read would view, or undefined when the invocation does something else. */
function readOperands(name: string, args: string[]): string[] | undefined {
  if (name === "cat") {
    const { options, operands } = split(args, /^$/);
    return options.every((option) => CAT_PLAIN.test(option)) ? operands : undefined;
  }
  if (name === "head" || name === "tail") {
    const { options, operands } = split(args, HEAD_TAIL_ARG);
    return options.some((option) => HEAD_TAIL_RAW.test(option)) ? undefined : operands;
  }
  if (name === "sed") {
    const { options, operands } = split(args, SED_ARG);
    if (!options.some((option) => /^(?:-n|--quiet|--silent)$/.test(option))) return;
    if (options.some((option) => /^(?:-f|--file)/.test(option))) return;
    const expression = options.findIndex((option) => /^(?:-e|--expression)$/.test(option));
    const script = expression >= 0 ? options[expression + 1] : operands.shift();
    return script !== undefined && SED_PRINT.test(script) ? operands : undefined;
  }
}

function isRegularFile(operand: string, cwd: string): boolean {
  if (operand === "-") return false;
  const expanded = operand.startsWith("~/") ? `${homedir()}${operand.slice(1)}` : operand;
  const path = isAbsolute(expanded) ? expanded : resolve(cwd, expanded);
  if (/^\/(?:proc|sys|dev)\//.test(path)) return false;
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

// `cat > file <<EOF` or `cat <<EOF > file`, and `tee file <<EOF`, at the start of a command line.
const HEREDOC_WRITE =
  /(?:^|[;&|\n])\s*(?:cat\b[^\n|;&]*?(?:<<[^\n|;&]*?[^&\d<]>|>[^&>][^\n|;&]*?<<)|tee\b[^\n|;&]*?<<)/;

/** The violation message for a model-issued bash command, or undefined to allow it. */
export function bashViolation(command: string, cwd: string): string | undefined {
  if (HEREDOC_WRITE.test(command)) return WRITE_MESSAGE;
  for (const segment of segments(command)) {
    // Only the executable is redirected. git grep and remote arguments are not local commands.
    const { words, elevated } = localInvocation(segment.words);
    const name = words[0]?.split("/").pop() ?? "";
    const args = words.slice(1);
    for (const rule of REDIRECTIONS) {
      if (name !== rule.command) continue;
      if (
        rule.option &&
        !args.some((word) => word === rule.option || word.startsWith(`${rule.option}=`))
      ) {
        continue;
      }
      return rule.message;
    }
    // File tools cannot touch root-owned files, and piped or redirected output is not a read.
    if (elevated) continue;
    if (name === "sed" && args.some((arg) => /^(?:-[nErsuz]*i|--in-place)/.test(arg))) {
      return EDIT_MESSAGE;
    }
    if (name === "perl" && args.some((arg) => /^-[0-9aplnsw]*i/.test(arg))) return EDIT_MESSAGE;
    if (segment.piped || segment.redirected) continue;
    const operands = readOperands(name, args);
    if (operands?.some((operand) => isRegularFile(operand, cwd))) return READ_MESSAGE;
  }
}

export default function toolGuards(pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;
    // CustomToolCallEvent keeps toolName from narrowing the input type.
    const command = (event.input as { command?: unknown }).command;
    if (typeof command !== "string") return;
    const message = bashViolation(command, ctx.cwd);
    if (message) return { block: true, reason: `TOOL USAGE VIOLATION: ${message}` };
  });
}
