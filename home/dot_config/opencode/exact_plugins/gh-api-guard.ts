import type { Plugin } from "@opencode-ai/plugin";

// Require an explicit method for every real `gh api` invocation. Permission rules
// separately allow conventional GET commands and ask for other methods.

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
  };
};
