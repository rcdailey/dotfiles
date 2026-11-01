import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { constants, cp, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";
import { git } from "./git.ts";

const execFileAsync = promisify(execFile);
const HOOK_TIMEOUT_MS = 30 * 60 * 1000;
const HOOK_OUTPUT_TAIL_LINES = 40;

const splitNul = (text: string) => text.split("\0").filter(Boolean);

async function ignoredByRepository(repository: string, paths: string[]) {
  try {
    const run = execFileAsync("git", ["check-ignore", "--stdin", "-z"], {
      cwd: repository,
      encoding: "utf8",
    });
    run.child.stdin?.end(paths.map((path) => `${path}\0`).join(""));
    const { stdout } = await run;
    return splitNul(stdout);
  } catch (error) {
    // check-ignore exits 1 when none of the paths are ignored.
    if ((error as { code?: unknown }).code === 1) return [];
    throw error;
  }
}

/**
 * Copies local files into a sandbox with worktrunk's `.worktreeinclude` semantics: an untracked
 * path is copied only when the repository ignores it and `.worktreeinclude` matches it. Wholly
 * matched directories copy as one entry. Returns the copied repository-relative paths.
 */
export async function copyIncludedFiles(repository: string, sandbox: string) {
  const include = join(repository, ".worktreeinclude");
  if (!existsSync(include)) return [];
  const listing = ["ls-files", "-z", "--others", "--ignored", "--directory"];
  const candidates = splitNul(await git(repository, [...listing, `--exclude-from=${include}`]));
  if (candidates.length === 0) return [];
  const included = await ignoredByRepository(repository, candidates);
  for (const path of included) {
    await cp(join(repository, path), join(sandbox, path), {
      recursive: true,
      force: false,
      preserveTimestamps: true,
      verbatimSymlinks: true,
      mode: constants.COPYFILE_FICLONE,
    });
  }
  return included;
}

const tail = (text: string) => text.trim().split("\n").slice(-HOOK_OUTPUT_TAIL_LINES).join("\n");

/**
 * Runs the sandbox's project `pre-start` hooks from `.config/wt.toml` without approval prompts.
 * An empty user config keeps the user's personal worktrunk hooks out of the sandbox.
 */
export async function runSetupHook(sandbox: string, stateDirectory: string) {
  if (!existsSync(join(sandbox, ".config", "wt.toml"))) return "absent (no .config/wt.toml)";
  const userConfig = join(stateDirectory, "wt-user.toml");
  await writeFile(userConfig, "");
  const args = [
    "-C",
    sandbox,
    "--config",
    userConfig,
    "hook",
    "pre-start",
    "--foreground",
    "--yes",
  ];
  try {
    await execFileAsync("wt", args, {
      encoding: "utf8",
      timeout: HOOK_TIMEOUT_MS,
      maxBuffer: 64 * 1024 * 1024,
    });
    return "ran";
  } catch (error) {
    const failure = error as { code?: unknown; stdout?: string; stderr?: string };
    if (failure.code === "ENOENT") return "unavailable (wt is not installed)";
    return `failed\n${tail(`${failure.stdout ?? ""}\n${failure.stderr ?? ""}`)}`;
  }
}
