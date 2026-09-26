import { spawn } from "node:child_process";

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
