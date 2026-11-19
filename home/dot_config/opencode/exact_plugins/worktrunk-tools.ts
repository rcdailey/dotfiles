import { execFile } from "node:child_process";
import path from "node:path";
import type { Plugin } from "@opencode/plugin";
import { DIRECT_TOOL } from "./lib/direct-tool.ts";

/**
 * Worktree tools backed by worktrunk (`wt`) that also move the calling session: into the worktree
 * on switch, and out of it before it disappears on remove or merge. They replace OpenCode's
 * built-in worktree tools, which cannot switch or merge and never move the session, so an agent
 * would otherwise spend extra calls on session_move or strand the session in a deleted directory.
 *
 * Moves are queued by OpenCode and take effect after the current step, so the tool result is the
 * last thing the agent sees from the old directory. Branch policy (mainline vs feature branch, PR
 * vs local merge) stays with the agent's instructions; these tools only run what they are asked.
 *
 * Worktrunk's own plugin (`worktrunk.ts`, installed by `wt config plugins opencode install`)
 * still provides activity markers and the strategy behind worktrees created from the OpenCode UI.
 */

const REPLACED = ["opencode_worktree_create", "opencode_worktree_list", "opencode_worktree_remove"];

/** Hidden from agents whose edit permission is wholly denied, since these change the checkout. */
const MUTATING = { ...DIRECT_TOOL, permission: "edit" } as const;

interface Run {
  ok: boolean;
  stdout: string;
  stderr: string;
}

interface Worktree {
  branch?: string;
  path: string;
  main: boolean;
  current: boolean;
}

/**
 * Runs wt in `directory` under that directory's mise environment. OpenCode's own environment is a
 * snapshot from service start, so worktrunk hooks (dependency restores, for example) would miss
 * the repository's tools without it. Nonzero exits resolve so callers can still read stdout.
 */
function wt(directory: string, args: string[], signal: AbortSignal): Promise<Run> {
  return new Promise((resolve, reject) => {
    execFile(
      "mise",
      ["exec", "-C", directory, "--", "wt", "-C", directory, ...args],
      {
        cwd: directory,
        signal,
        maxBuffer: 16 * 1024 * 1024,
        env: { ...process.env, NO_COLOR: "1", CLICOLOR: "0" },
      },
      (error, stdout, stderr) => {
        // A missing executable or an abort has no exit code and no wt output worth reporting
        if (error && typeof error.code !== "number") reject(error);
        else resolve({ ok: !error, stdout, stderr });
      },
    );
  });
}

// wt asks for shell integration whenever it cannot cd; the session move replaces that cd
const CD_HINT = /cannot change directory|wt config shell install/;

const text = (run: Run) =>
  [run.stderr, run.stdout]
    .join("\n")
    .split("\n")
    .filter((line) => line.trim() && !CD_HINT.test(line))
    .join("\n");

function check(run: Run, command: string): Run {
  if (!run.ok) throw new Error(text(run) || `wt ${command} failed`);
  return run;
}

async function worktrees(directory: string, signal: AbortSignal): Promise<Worktree[]> {
  const { stdout } = check(await wt(directory, ["list", "--format=json"], signal), "list");
  const { items } = JSON.parse(stdout) as {
    items: {
      branch?: string | null;
      worktree?: { path: string; main: boolean; current: boolean };
    }[];
  };
  return items.flatMap(({ branch, worktree }) =>
    worktree ? [{ branch: branch ?? undefined, ...worktree }] : [],
  );
}

const within = (parent: string, child: string) => {
  const relative = path.relative(parent, child);
  return !relative.startsWith("..") && !path.isAbsolute(relative);
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

function field<T extends "string" | "boolean">(input: unknown, key: string, type: T) {
  const value = isRecord(input) ? input[key] : undefined;
  if (value === undefined || value === "") return undefined;
  if (typeof value !== type) throw new Error(`${key} must be a ${type}`);
  return value as T extends "string" ? string : boolean;
}

export const WorktrunkTools = {
  id: "local.worktrunk-tools",
  async setup(ctx) {
    const directoryOf = async (sessionID: string) =>
      (await ctx.session.get({ sessionID })).location.directory as string;

    const moveTo = async (sessionID: string, from: string, to: string) => {
      if (path.resolve(from) === path.resolve(to)) return "";
      await ctx.session.move({ sessionID, directory: to, delivery: "steer" } as Parameters<
        typeof ctx.session.move
      >[0]);
      return `The session moves to ${to} after this call.`;
    };

    await ctx.tool.transform((tools) => {
      for (const id of REPLACED) tools.remove(id);

      tools.add({
        name: "wt_switch",
        description:
          "Switch to a branch's worktree with worktrunk, creating the worktree (and, with " +
          "create, the branch) when missing, and move this session into it. Runs the " +
          "repository's worktrunk hooks. The worktree path comes from worktrunk's path template.",
        input: {
          type: "object",
          properties: {
            branch: { type: "string", description: "Branch name" },
            create: { type: "boolean", description: "Create a new branch" },
            base: { type: "string", description: "Starting ref for a new branch" },
          },
          required: ["branch"],
          additionalProperties: false,
        },
        options: MUTATING,
        async execute(input, context) {
          const branch = field(input, "branch", "string");
          if (!branch) throw new Error("branch is required");
          const directory = await directoryOf(context.sessionID);
          const args = ["switch", branch, "--no-cd", "--format=json"];
          if (field(input, "create", "boolean")) args.push("--create");
          const base = field(input, "base", "string");
          if (base) args.push("--base", base);

          const run = await wt(directory, args, context.signal);
          // A worktree created before a failing hook is still reported on stdout
          let worktree: string | undefined;
          try {
            worktree = (JSON.parse(run.stdout) as { path?: string }).path;
          } catch {
            worktree = undefined;
          }
          if (!worktree) throw new Error(text(run) || "wt switch failed");
          const moved = await moveTo(context.sessionID, directory, worktree);
          const status = run.ok
            ? `Switched to ${branch} in ${worktree}.`
            : `The worktree ${worktree} exists, but wt switch failed:\n${run.stderr.trim()}`;
          return { content: [status, moved].filter(Boolean).join("\n") };
        },
      });

      tools.add({
        name: "wt_list",
        description: "List the repository's worktrees and their branch status with worktrunk.",
        input: { type: "object", properties: {}, additionalProperties: false },
        options: DIRECT_TOOL,
        async execute(_input, context) {
          const directory = await directoryOf(context.sessionID);
          return { content: text(check(await wt(directory, ["list"], context.signal), "list")) };
        },
      });

      tools.add({
        name: "wt_remove",
        description:
          "Remove a worktree with worktrunk, deleting its branch when merged. Removing the " +
          "session's own worktree moves the session to the main checkout. Fails on " +
          "uncommitted changes unless force is set.",
        input: {
          type: "object",
          properties: {
            branch: {
              type: "string",
              description: "Branch whose worktree to remove; defaults to the session's worktree",
            },
            force: { type: "boolean", description: "Discard uncommitted and untracked files" },
          },
          additionalProperties: false,
        },
        options: MUTATING,
        async execute(input, context) {
          const branch = field(input, "branch", "string");
          const directory = await directoryOf(context.sessionID);
          const list = await worktrees(directory, context.signal);
          const target = list.find((w) => (branch ? w.branch === branch : w.current));
          if (!target) {
            throw new Error(branch ? `No worktree has branch ${branch}` : "Not in a worktree");
          }
          if (target.main) throw new Error("The main checkout cannot be removed");
          const main = list.find((w) => w.main)?.path;
          const leaving = main !== undefined && within(target.path, directory);

          // Run from the main checkout when the session's own directory is being deleted
          const args = ["remove", "--foreground", target.path];
          if (field(input, "force", "boolean")) args.push("--force");
          const run = check(await wt(leaving ? main : directory, args, context.signal), "remove");
          const moved = leaving ? await moveTo(context.sessionID, directory, main) : "";
          return { content: [text(run), moved].filter(Boolean).join("\n") };
        },
      });

      tools.add({
        name: "wt_merge",
        description:
          "Merge the session's worktree branch into the target branch with worktrunk (commit " +
          "pending changes, rebase, fast-forward the target, remove the worktree) and move the " +
          "session to the target branch's checkout. Runs the repository's merge hooks. Merges " +
          "locally only; it does not push or open a pull request.",
        input: {
          type: "object",
          properties: {
            target: {
              type: "string",
              description: "Target branch; defaults to the default branch",
            },
            squash: {
              type: "boolean",
              description: "false keeps each commit; omit to use worktrunk's configured default",
            },
          },
          additionalProperties: false,
        },
        options: MUTATING,
        async execute(input, context) {
          const directory = await directoryOf(context.sessionID);
          const list = await worktrees(directory, context.signal);
          const source = list.find((w) => w.current);
          if (!source || source.main) throw new Error("The session is not in a linked worktree");

          let target = field(input, "target", "string");
          const args = ["merge"];
          if (target) args.push(target);
          if (field(input, "squash", "boolean") === false) args.push("--no-squash");
          target ??= check(
            await wt(directory, ["config", "state", "default-branch"], context.signal),
            "config state default-branch",
          ).stdout.trim();
          const destination =
            list.find((w) => w.branch === target)?.path ?? list.find((w) => w.main)?.path;

          const run = check(await wt(directory, args, context.signal), "merge");
          const moved = destination ? await moveTo(context.sessionID, directory, destination) : "";
          return { content: [text(run), moved].filter(Boolean).join("\n") };
        },
      });
    });
  },
} satisfies Plugin.Plugin;

export default WorktrunkTools;
