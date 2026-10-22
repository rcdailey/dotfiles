import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import type { Plugin } from "@opencode/plugin";

const run = promisify(execFile);

// Applies the same transition an interactive shell makes on cd: hook-env reverts the variables the
// previous directory's mise config set (tracked in __MISE_DIFF) and applies the target directory's
// tools and [env]. --noprofile/--norc and no BASH_ENV keep startup files out of the result. The
// assignment keeps mise's exit status, which `eval "$(...)"` would discard.
const SCRIPT = 'hook=$(mise hook-env -s bash --force 2>/dev/null) && eval "$hook" && env -0';
// Variables bash itself sets; they describe the helper shell, not the mise environment.
const SHELL_OWNED = new Set(["_", "PWD", "OLDPWD", "SHLVL"]);

function parseEnv(output: string): Map<string, string> {
  const vars = new Map<string, string>();
  for (const entry of output.split("\0")) {
    const eq = entry.indexOf("=");
    if (eq > 0) vars.set(entry.slice(0, eq), entry.slice(eq + 1));
  }
  return vars;
}

/**
 * Gives every agent shell command the mise environment (tool PATH and [env] variables) of its own
 * working directory. Without it, commands inherit a snapshot taken when the TUI started, so they
 * miss other repos' tools and secrets and ignore mise.toml edits made since. When mise is missing
 * or fails, the command runs with the env it would have had anyway.
 *
 * Local MCP servers start once with the OpenCode service's env (whichever shell started the
 * service), in their project directory. Prefixing their command with `mise exec --` applies that
 * directory's mise env instead. Remote servers are untouched: their only local inputs are
 * {env:...} config substitutions, which read the service env.
 */
export const MiseEnv = {
  id: "local.mise-env",
  async setup(ctx) {
    await ctx.shell.hook("create.before", async (invocation) => {
      const { BASH_ENV: _, ...env } = invocation.env;
      let output: string;
      try {
        ({ stdout: output } = await run("bash", ["--noprofile", "--norc", "-c", SCRIPT], {
          cwd: path.resolve(ctx.location.directory, invocation.cwd),
          env,
          maxBuffer: 16 * 1024 * 1024,
          timeout: 10_000,
        }));
      } catch {
        return;
      }
      const next = parseEnv(output);
      for (const key of Object.keys(invocation.env)) {
        if (!SHELL_OWNED.has(key) && !next.has(key)) delete invocation.env[key];
      }
      for (const [key, value] of next) {
        if (!SHELL_OWNED.has(key)) invocation.env[key] = value;
      }
    });

    await ctx.mcp.transform((editor) => {
      for (const [, server] of editor.list()) {
        if (server.type !== "local") continue;
        // Transforms rerun on config reload; OpenCode special-cases a bare `opencode` command
        const [command] = server.command;
        if (command === "mise" || command === "opencode") continue;
        // mise exec overwrites inherited variables its [env] also sets; re-applying the server's
        // own environment after it keeps explicit config values winning
        const assignments = Object.entries(server.environment ?? {}).map(([k, v]) => `${k}=${v}`);
        const prefix = assignments.length > 0 ? ["env", ...assignments] : [];
        server.command = ["mise", "exec", "--", ...prefix, ...server.command];
      }
    });
  },
} satisfies Plugin.Plugin;

export default MiseEnv;
