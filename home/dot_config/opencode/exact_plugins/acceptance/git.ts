import { execFile } from "node:child_process";
import { realpath, rm } from "node:fs/promises";
import { devNull } from "node:os";
import { delimiter, join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const MAX_OUTPUT_BYTES = 256 * 1024 * 1024;

/** A snapshot operation could not be completed safely; the message is shown to the agent. */
export class SnapshotError extends Error {}

export async function git(cwd: string, args: string[], env?: NodeJS.ProcessEnv) {
  try {
    const { stdout } = await execFileAsync("git", args, {
      cwd,
      env,
      encoding: "utf8",
      maxBuffer: MAX_OUTPUT_BYTES,
    });
    return stdout;
  } catch (error) {
    const failure = error as { code?: unknown; stderr?: string; stdout?: string };
    if (failure.code === "ENOENT") throw new SnapshotError("git not found; install it first");
    const message = failure.stderr?.trim() || failure.stdout?.trim();
    throw new SnapshotError(message || `git ${args.join(" ")} failed`);
  }
}

export async function repositoryRoot(directory: string) {
  const root = await git(directory, ["rev-parse", "--show-toplevel"]);
  return realpath(root.trim());
}

export async function resolveTree(repository: string, revision: string) {
  return (await git(repository, ["rev-parse", "--verify", `${revision}^{tree}`])).trim();
}

async function unbornHead(repository: string) {
  let branch: string;
  try {
    branch = (await git(repository, ["symbolic-ref", "--quiet", "HEAD"])).trim();
  } catch {
    return false;
  }
  try {
    await git(repository, ["show-ref", "--verify", "--quiet", branch]);
    return false;
  } catch {
    return true;
  }
}

/** Resolves HEAD's tree, or Git's empty tree while the current branch has no commits. */
export async function headTree(repository: string) {
  try {
    return await resolveTree(repository, "HEAD");
  } catch (error) {
    if (!(await unbornHead(repository))) throw error;
  }
  return (await git(repository, ["hash-object", "-t", "tree", devNull])).trim();
}

// Snapshot objects live in the state directory; the repository's objects stay readable as an
// alternate, so captures never write to the repository's index or object store.
async function snapshotEnvironment(repository: string, stateDirectory: string) {
  const objects = await git(repository, [
    "rev-parse",
    "--path-format=absolute",
    "--git-path",
    "objects",
  ]);
  const alternates = [objects.trim(), process.env.GIT_ALTERNATE_OBJECT_DIRECTORIES]
    .filter(Boolean)
    .join(delimiter);
  return {
    ...process.env,
    GIT_ALTERNATE_OBJECT_DIRECTORIES: alternates,
    GIT_OBJECT_DIRECTORY: join(stateDirectory, "objects"),
  };
}

/** Captures the nonignored filesystem state as a private Git tree. */
export async function captureTree(repository: string, stateDirectory: string, indexName: string) {
  const index = join(stateDirectory, indexName);
  const cleanup = () =>
    Promise.all([rm(index, { force: true }), rm(`${index}.lock`, { force: true })]);
  await cleanup();
  const env = { ...(await snapshotEnvironment(repository, stateDirectory)), GIT_INDEX_FILE: index };
  try {
    await git(repository, ["read-tree", await headTree(repository)], env);
    await git(repository, ["add", "-A", "--", "."], env);
    return (await git(repository, ["write-tree"], env)).trim();
  } finally {
    await cleanup();
  }
}

const DIFF_FLAGS = ["diff", "--no-color", "--no-ext-diff", "--no-textconv", "--find-renames"];

/** Returns Git's concise changed-path inventory between two trees. */
export async function changedPaths(
  repository: string,
  stateDirectory: string,
  previousTree: string,
  currentTree: string,
) {
  const env = await snapshotEnvironment(repository, stateDirectory);
  const args = [...DIFF_FLAGS, "--name-status", previousTree, currentTree];
  return (await git(repository, args, env)).trim();
}

/** Returns a targeted Git patch between two snapshot trees. */
export async function treeDiff(
  repository: string,
  stateDirectory: string,
  previousTree: string,
  currentTree: string,
  paths: string[],
) {
  const env = await snapshotEnvironment(repository, stateDirectory);
  const range = [previousTree, currentTree, "--", ...paths];
  return git(repository, [...DIFF_FLAGS, "--binary", "--full-index", ...range], env);
}
