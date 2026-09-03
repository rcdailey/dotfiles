import type { Plugin } from "@opencode-ai/plugin";

// Self-contained `gh api` permission semantics. The config only needs a single
// `"*gh api*": "ask"` bash rule; this plugin decides the outcome by parsing the
// command, because glob patterns match the raw string and cannot tell an actual
// `gh api` invocation from the literal text inside a quoted argument (e.g.
// `rg "gh api.*deployments"`). Delete this file to drop the behavior entirely.
//
// Read-only subagents (acceptance, reviewer) keep their own agent-level `gh api`
// denies on purpose: a hard deny fails fast, while an `ask` stalls an unattended
// subagent. Those requests never reach `ask`, so this plugin cannot relax them.

interface Token {
  value: string;
  quoted: boolean;
}

const OPERATORS = ["&&", "||", "|", ";", "(", ")"];

// Tokenizes a shell command into operator-delimited segments. Quoted tokens keep
// their content but are flagged, so quoted text is never treated as a command.
function segments(input: string): Token[][] {
  const result: Token[][] = [[]];
  let buf = "";
  let quoted = false;
  let open = false;

  const flush = () => {
    if (open) result[result.length - 1].push({ value: buf, quoted });
    buf = "";
    quoted = false;
    open = false;
  };

  for (let i = 0; i < input.length; ) {
    const ch = input[i];

    if (ch === "'" || ch === '"') {
      open = true;
      quoted = true;
      i++;
      while (i < input.length && input[i] !== ch) {
        if (ch === '"' && input[i] === "\\") i++;
        buf += input[i];
        i++;
      }
      i++;
      continue;
    }

    if (ch === "\\") {
      open = true;
      buf += input[i + 1] ?? "";
      i += 2;
      continue;
    }

    if (/\s/.test(ch)) {
      flush();
      if (ch === "\n") result.push([]);
      i++;
      continue;
    }

    const op = OPERATORS.find((candidate) => input.startsWith(candidate, i));
    if (op) {
      flush();
      result.push([]);
      i += op.length;
      continue;
    }

    open = true;
    buf += ch;
    i++;
  }

  flush();
  return result.filter((tokens) => tokens.length > 0);
}

function basename(value: string): string {
  return value.includes("/") ? (value.split("/").pop() ?? value) : value;
}

// Commands that execute a nested command line we cannot parse. Known ceiling:
// `gh api` inside such an argument stays an "ask" instead of being classified.
const NESTED_SHELL = /^(sh|bash|zsh|dash|ksh|fish|eval|ssh|docker|podman|kubectl|talosctl)$/;

function leadingCommand(tokens: Token[]): Token | undefined {
  return tokens.find((token) => !(token.quoted || /^[A-Za-z_][A-Za-z0-9_]*=/.test(token.value)));
}

// Args following each real `gh api` invocation in the command. Scanning every
// token (not just the leading one) covers wrappers like `xargs -I{} gh api ...`.
function invocations(command: string): Token[][] {
  const found: Token[][] = [];
  for (const tokens of segments(command)) {
    for (let i = 0; i < tokens.length - 1; i++) {
      if (tokens[i].quoted || basename(tokens[i].value) !== "gh") continue;
      if (tokens[i + 1].quoted || tokens[i + 1].value !== "api") continue;
      found.push(tokens.slice(i + 2));
    }
  }
  return found;
}

function hidesGhApi(command: string): boolean {
  return segments(command).some((tokens) => {
    const lead = leadingCommand(tokens);
    if (!lead || !NESTED_SHELL.test(basename(lead.value))) return false;
    return tokens.some((token) => token.quoted && token.value.includes("gh api"));
  });
}

function methodOf(args: Token[]): string | undefined {
  for (let i = 0; i < args.length; i++) {
    const arg = args[i].value;
    if (arg === "--method" || arg === "-X") return args[i + 1]?.value;
    const inline = /^(?:--method|-X)=(.+)$/.exec(arg);
    if (inline) return inline[1];
  }
  return undefined;
}

const MISSING_METHOD =
  "TOOL USAGE VIOLATION: 'gh api' requires an explicit --method\n" +
  "Correct: gh api --method GET repos/{owner}/{repo}/pulls";

export const GhApiGuard: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;

      const command = output.args?.command as string | undefined;
      if (!command) return;

      for (const args of invocations(command)) {
        if (!methodOf(args)) throw new Error(MISSING_METHOD);
      }
    },

    "permission.ask": async (input, output) => {
      if (output.status !== "ask") return;

      const command = input.metadata?.command;
      if (typeof command !== "string") return;

      // Only relax requests our own bash rule could have raised, so an unrelated
      // pattern in the same request (e.g. `git push`) still prompts.
      const patterns = [input.pattern ?? []].flat();
      if (!patterns.length || !patterns.every((p) => p.includes("gh api"))) return;

      if (hidesGhApi(command)) return;

      const calls = invocations(command);
      if (calls.some((args) => methodOf(args)?.toUpperCase() !== "GET")) return;

      output.status = "allow";
    },
  };
};
