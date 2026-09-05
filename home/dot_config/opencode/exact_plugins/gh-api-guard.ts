import type { Plugin } from "@opencode-ai/plugin";

// Self-contained `gh api` permission semantics. The config only needs a single
// `"*gh api*": "ask"` bash rule; this plugin decides the outcome by parsing the
// command. Auto-approval covers only literal direct REST reads and inert rg searches.
// Shell expansion, composition, and unknown wrappers retain approval. This is not a
// shell sandbox; broader automatic approval requires a structured execution boundary.
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

// Complete literal words only: no expansions, redirections, comments, or shell operators.
const LITERAL_COMMAND = /^(?:[ \t]|'[^'\n]*'|"[^"\\$`\n]*"|[^\s'"\\$`|&;()<>#*?[\]{}~!])+$/;

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

function methodOf(args: Token[]): string | undefined {
  for (let i = 0; i < args.length; i++) {
    const arg = args[i].value;
    if (arg === "--method" || arg === "-X") return args[i + 1]?.value;
    const inline = /^(?:--method=|-X=?)(.+)$/.exec(arg);
    if (inline) return inline[1];
  }
  return undefined;
}

function isLiteralRead(command: string): boolean {
  if (!LITERAL_COMMAND.test(command)) return false;
  const parts = segments(command);
  if (parts.length !== 1) return false;
  const [lead, subcommand, ...args] = parts[0];
  if (!lead || lead.quoted) return false;

  if (lead.value === "rg") {
    return !parts[0].some((token) => /^--pre(?:=|$)/.test(token.value));
  }
  if (lead.value !== "gh" || subcommand?.quoted || subcommand?.value !== "api") return false;
  if (args.some((token) => /^\/?graphql(?:[/?]|$)/.test(token.value))) return false;

  // Do not mistake a field value for an option, or miss method overrides in short clusters.
  const methods = args.filter((token) => /^(?:--method(?:=|$)|-X)/.test(token.value));
  if (methods.length !== 1 || methodOf(args) !== "GET") return false;
  const index = args.indexOf(methods[0]);
  if (index > 1 || (index === 1 && args[0].value.startsWith("-"))) return false;
  return !args.some((token) => /^-[^-].+/.test(token.value) && !/^-X=?GET$/.test(token.value));
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

      if (!isLiteralRead(command)) return;

      output.status = "allow";
    },
  };
};
