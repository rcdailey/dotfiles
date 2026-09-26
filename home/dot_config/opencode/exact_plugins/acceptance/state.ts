import { createHash, randomUUID } from "node:crypto";
import { chmod, lstat, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  captureTree,
  changedPaths,
  headTree,
  repositoryRoot,
  resolveTree,
  SnapshotError,
  treeDiff,
} from "./git.ts";

const SCHEMA_VERSION = 1;

interface SnapshotState {
  version: number;
  repository: string;
  base_tree: string;
  audited_tree: string | null;
  pending_tree: string | null;
  iteration: number;
}

const previousTree = (state: SnapshotState) => state.audited_tree ?? state.base_tree;

async function secureDirectory(path: string) {
  try {
    await mkdir(path, { mode: 0o700 });
    return;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
  }
  const info = await lstat(path);
  if (!info.isDirectory() || info.isSymbolicLink()) {
    throw new SnapshotError(`unsafe state path: ${path}`);
  }
  if (info.uid !== process.getuid?.()) {
    throw new SnapshotError(`state path is owned by another user: ${path}`);
  }
  await chmod(path, 0o700);
}

async function stateDirectory(sessionID: string) {
  if (!sessionID) throw new SnapshotError("session ID is missing");
  const root = join(tmpdir(), "opencode-acceptance");
  await secureDirectory(root);
  const directory = join(root, createHash("sha256").update(sessionID).digest("hex"));
  await secureDirectory(directory);
  await secureDirectory(join(directory, "objects"));
  return directory;
}

const isTree = (value: unknown) => typeof value === "string" && value.length > 0;

async function loadState(directory: string) {
  let text: string;
  try {
    text = await readFile(join(directory, "state.json"), "utf8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
    throw new SnapshotError(`invalid snapshot state: ${(error as Error).message}`);
  }
  let state: SnapshotState;
  try {
    state = JSON.parse(text);
  } catch (error) {
    throw new SnapshotError(`invalid snapshot state: ${(error as Error).message}`);
  }
  if (state?.version !== SCHEMA_VERSION) {
    throw new SnapshotError(`unsupported snapshot state version: ${state?.version}`);
  }
  if (!isTree(state.repository)) throw new SnapshotError("invalid snapshot repository");
  if (!isTree(state.base_tree)) throw new SnapshotError("invalid snapshot base tree");
  if (state.audited_tree !== null && !isTree(state.audited_tree)) {
    throw new SnapshotError("invalid snapshot audited tree");
  }
  if (state.pending_tree !== null && !isTree(state.pending_tree)) {
    throw new SnapshotError("invalid snapshot pending tree");
  }
  if (!Number.isInteger(state.iteration) || state.iteration < 0) {
    throw new SnapshotError("invalid snapshot iteration");
  }
  return state;
}

async function saveState(directory: string, state: SnapshotState) {
  const temporary = join(directory, `state.${randomUUID()}`);
  try {
    await writeFile(temporary, `${JSON.stringify(state)}\n`, { mode: 0o600, flag: "wx" });
    await rename(temporary, join(directory, "state.json"));
  } finally {
    await rm(temporary, { force: true });
  }
}

// Serializes operations per session within this OpenCode server. Ceiling: two server processes
// sharing one session would need a cross-process lock; OpenCode runs a session in one server.
const queues = new Map<string, Promise<unknown>>();

function locked<T>(directory: string, operation: () => Promise<T>) {
  const previous = queues.get(directory) ?? Promise.resolve();
  const result = previous.catch(() => undefined).then(operation);
  const settled = result.catch(() => undefined);
  queues.set(directory, settled);
  void settled.then(() => {
    if (queues.get(directory) === settled) queues.delete(directory);
  });
  return result;
}

async function validatedState(directory: string, repository: string, base?: string) {
  const state = await loadState(directory);
  if (!state) {
    return {
      version: SCHEMA_VERSION,
      repository,
      base_tree: base ? await resolveTree(repository, base) : await headTree(repository),
      audited_tree: null,
      pending_tree: null,
      iteration: 0,
    } satisfies SnapshotState;
  }
  if (state.repository !== repository) {
    throw new SnapshotError(`session belongs to ${state.repository}, not ${repository}`);
  }
  if (base && state.base_tree !== (await resolveTree(repository, base))) {
    throw new SnapshotError("Base differs from the existing acceptance session");
  }
  return state;
}

function pendingTree(state: SnapshotState) {
  if (!state.pending_tree) {
    throw new SnapshotError("no pending acceptance iteration; run acceptance_begin first");
  }
  return state.pending_tree;
}

/** Identifies the acceptance session and the repository containing the working directory. */
export interface Scope {
  sessionID: string;
  directory: string;
}

async function prepare(scope: Scope) {
  return {
    repository: await repositoryRoot(scope.directory),
    directory: await stateDirectory(scope.sessionID),
  };
}

/** Captures the candidate tree and reports changes since the last audited tree. */
export async function begin(scope: Scope, base?: string) {
  const { repository, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, repository, base);
    state.pending_tree = await captureTree(repository, directory, "pending.index");
    await saveState(directory, state);
    const previous = previousTree(state);
    const changes = await changedPaths(repository, directory, previous, state.pending_tree);
    return [
      `Iteration: ${state.iteration + 1}`,
      `Previous tree: ${previous}`,
      `Pending tree: ${state.pending_tree}`,
      "Changes:",
      changes || "(none)",
    ].join("\n");
  });
}

/** Returns the pending iteration's patch for the given repository paths. */
export async function diff(scope: Scope, paths: string[]) {
  if (paths.length === 0) throw new SnapshotError("at least one path is required");
  const { repository, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, repository);
    const pending = pendingTree(state);
    const patch = await treeDiff(repository, directory, previousTree(state), pending, paths);
    return patch || "(no changes)";
  });
}

/** Promotes the pending tree to audited and reports whether the repository still matches it. */
export async function finish(scope: Scope) {
  const { repository, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, repository);
    const audited = pendingTree(state);
    const current = await captureTree(repository, directory, "verify.index");
    const changes = await changedPaths(repository, directory, audited, current);
    state.audited_tree = audited;
    state.pending_tree = null;
    state.iteration += 1;
    await saveState(directory, state);
    const lines = [
      `Iteration: ${state.iteration}`,
      `Audited tree: ${audited}`,
      `Current tree: ${current}`,
    ];
    if (audited === current) return [...lines, "Result: stable"].join("\n");
    return [...lines, "Result: retry", "Changes since capture:", changes || "(none)"].join("\n");
  });
}
