import { spawn } from "node:child_process";

/** A research CLI invocation failed; the message carries the CLI's combined output. */
export class ResearchError extends Error {}

/**
 * Runs the `research` CLI with the budget and ledgers scoped to one OpenCode session. The CLI
 * reads the session from OPENCODE_SESSION_ID; without it, budgets and ledgers are disabled.
 * `requireGoals` makes retrieval refuse until the session records goals and makes the closing
 * ledger check a goal report; only agents whose prompt follows that protocol may set it.
 */
export function runResearch(
  sessionID: string,
  args: string[],
  signal?: AbortSignal,
  requireGoals = false,
) {
  return new Promise<string>((resolve, reject) => {
    const env: NodeJS.ProcessEnv = { ...process.env, OPENCODE_SESSION_ID: sessionID };
    if (requireGoals) env.RESEARCH_REQUIRE_GOALS = "1";
    const child = spawn("research", args, {
      env,
      stdio: ["ignore", "pipe", "pipe"],
      signal,
    });
    // Warnings and errors go to stderr and results to stdout; keep them in arrival order.
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
