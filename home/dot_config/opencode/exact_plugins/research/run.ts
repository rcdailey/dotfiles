import { spawn } from "node:child_process";

/**
 * Splits one command-line string into words with POSIX shell quoting rules (single quotes,
 * double quotes, backslash escapes). Models sometimes send tool arguments as one string; passing
 * it through unsplit would hand the CLI a single positional value.
 */
export function shellWords(line: string) {
  const words: string[] = [];
  let word = "";
  let started = false;
  let quote: string | undefined;
  for (let index = 0; index < line.length; index++) {
    const char = line[index] as string;
    if (quote) {
      if (char === quote) quote = undefined;
      else if (char === "\\" && quote === '"' && index + 1 < line.length) word += line[++index];
      else word += char;
    } else if (char === "'" || char === '"') {
      quote = char;
      started = true;
    } else if (char === "\\" && index + 1 < line.length) {
      word += line[++index];
      started = true;
    } else if (/\s/.test(char)) {
      if (started) words.push(word);
      word = "";
      started = false;
    } else {
      word += char;
      started = true;
    }
  }
  if (started) words.push(word);
  return words;
}

/** A research CLI invocation failed; the message carries the CLI's combined output. */
export class ResearchError extends Error {}

/**
 * Runs the `research` CLI with the budget and ledgers scoped to one OpenCode session. The CLI
 * reads the session from OPENCODE_SESSION_ID; without it, budgets and ledgers are disabled.
 */
export function runResearch(sessionID: string, args: string[], signal?: AbortSignal) {
  return new Promise<string>((resolve, reject) => {
    const child = spawn("research", args, {
      env: { ...process.env, OPENCODE_SESSION_ID: sessionID },
      stdio: ["ignore", "pipe", "pipe"],
      signal,
    });
    // Reroute notices go to stderr and results to stdout; keep them in arrival order.
    const chunks: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => chunks.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => chunks.push(chunk));
    child.on("error", (error) => {
      const missing = (error as NodeJS.ErrnoException).code === "ENOENT";
      reject(missing ? new ResearchError("research CLI not found on PATH") : error);
    });
    child.on("close", (code) => {
      const output = Buffer.concat(chunks).toString("utf8").trim();
      if (code === 0) resolve(output);
      else reject(new ResearchError(output || `research exited with status ${code}`));
    });
  });
}
