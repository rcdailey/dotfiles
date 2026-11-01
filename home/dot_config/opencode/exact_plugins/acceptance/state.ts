import { createHash, randomUUID } from "node:crypto";
import { chmod, lstat, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import {
  captureTree,
  changedPaths,
  headTree,
  materializeWorkspace,
  repositoryRoot,
  resolveTree,
  SnapshotError,
  treeDiff,
} from "./git.ts";
import { copyIncludedFiles, runSetupHook } from "./sandbox.ts";

const SCHEMA_VERSION = 2;

interface RepositoryState {
  path: string;
  base_tree: string;
  audited_tree: string | null;
  pending_tree: string | null;
}

export const VERDICTS = ["pass", "fail", "incomplete"] as const;
export const CASE_STATUSES = ["pass", "fail", "unknown", "accepted gap"] as const;

/**
 * One acceptance case's outcome. `paths` are the repository paths its evidence depends on, written
 * `name:path` for non-primary repositories; a later iteration that changes one marks it stale.
 */
export interface LedgerEntry {
  case: string;
  status: (typeof CASE_STATUSES)[number];
  evidence: string;
  paths: string[];
}

/**
 * The primary repository is the session's working directory. Every repository, primary included,
 * is keyed by its directory basename, which prefixes its paths in tool input and ledger entries.
 * One iteration counter and ledger cover all repositories because they audit one goal.
 */
interface SnapshotState {
  version: number;
  primary: string;
  repositories: Record<string, RepositoryState>;
  iteration: number;
  verdict: (typeof VERDICTS)[number] | null;
  ledger: LedgerEntry[];
}

/** An additional repository named by the caller, relative to the session's directory. */
export interface RepositoryInput {
  path: string;
  base?: string;
}

const previousTree = (repository: RepositoryState) =>
  repository.audited_tree ?? repository.base_tree;

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
    throw new SnapshotError(
      `unsupported snapshot state version ${state?.version}; a fresh audit is required`,
    );
  }
  const repositories = Object.entries(state.repositories ?? {});
  if (!state.repositories?.[state.primary]) throw new SnapshotError("invalid snapshot primary");
  for (const [name, repository] of repositories) {
    if (!isTree(repository.path)) throw new SnapshotError(`invalid snapshot path for ${name}`);
    if (!isTree(repository.base_tree)) throw new SnapshotError(`invalid base tree for ${name}`);
    for (const tree of [repository.audited_tree, repository.pending_tree]) {
      if (tree !== null && !isTree(tree)) throw new SnapshotError(`invalid tree for ${name}`);
    }
  }
  if (!Number.isInteger(state.iteration) || state.iteration < 0) {
    throw new SnapshotError("invalid snapshot iteration");
  }
  if (!Array.isArray(state.ledger)) throw new SnapshotError("invalid snapshot ledger");
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

async function newRepository(path: string, base?: string): Promise<RepositoryState> {
  return {
    path,
    base_tree: base ? await resolveTree(path, base) : await headTree(path),
    audited_tree: null,
    pending_tree: null,
  };
}

async function checkBase(name: string, repository: RepositoryState, base?: string) {
  if (base && repository.base_tree !== (await resolveTree(repository.path, base))) {
    throw new SnapshotError(`Base for ${name} differs from the existing acceptance session`);
  }
}

/** Adds or confirms caller-named repositories; a resumed session may add but never move one. */
async function addRepositories(state: SnapshotState, scope: Scope, inputs: RepositoryInput[]) {
  for (const input of inputs) {
    const path = await repositoryRoot(resolve(scope.directory, input.path));
    const name = basename(path);
    const existing = state.repositories[name];
    if (!existing) {
      state.repositories[name] = await newRepository(path, input.base);
      continue;
    }
    if (existing.path !== path) {
      throw new SnapshotError(`repository name ${name} is already used by ${existing.path}`);
    }
    await checkBase(name, existing, input.base);
  }
}

async function validatedState(directory: string, primaryPath: string, base?: string) {
  const state = await loadState(directory);
  const primary = basename(primaryPath);
  if (!state) {
    return {
      version: SCHEMA_VERSION,
      primary,
      repositories: { [primary]: await newRepository(primaryPath, base) },
      iteration: 0,
      verdict: null,
      ledger: [],
    } satisfies SnapshotState;
  }
  const stored = state.repositories[state.primary];
  if (state.primary !== primary || stored?.path !== primaryPath) {
    throw new SnapshotError(`session belongs to ${stored?.path}, not ${primaryPath}`);
  }
  await checkBase(primary, stored, base);
  return state;
}

function pendingTree(name: string, repository: RepositoryState) {
  if (!repository.pending_tree) {
    throw new SnapshotError(`no pending acceptance iteration for ${name}; run acceptance_begin`);
  }
  return repository.pending_tree;
}

/** Identifies the acceptance session and the repository containing the working directory. */
export interface Scope {
  sessionID: string;
  directory: string;
}

async function prepare(scope: Scope) {
  return {
    primaryPath: await repositoryRoot(scope.directory),
    directory: await stateDirectory(scope.sessionID),
  };
}

const qualify = (state: SnapshotState, name: string, path: string) =>
  name === state.primary ? path : `${name}:${path}`;

/** Splits `name:path`; a path without a known repository prefix belongs to the primary. */
function splitPath(state: SnapshotState, path: string) {
  const separator = path.indexOf(":");
  const prefix = separator > 0 ? path.slice(0, separator) : "";
  if (prefix && state.repositories[prefix])
    return { name: prefix, path: path.slice(separator + 1) };
  if (prefix && !prefix.includes("/") && !prefix.includes("(")) {
    const known = Object.keys(state.repositories).join(", ");
    throw new SnapshotError(`unknown repository ${prefix}; known repositories: ${known}`);
  }
  return { name: state.primary, path };
}

const changedPathList = (nameStatus: string) =>
  nameStatus
    .split("\n")
    .filter(Boolean)
    .flatMap((line) => line.split("\t").slice(1));

function isStale(state: SnapshotState, entry: LedgerEntry, changed: Set<string>) {
  return entry.paths.some((raw) => {
    const { name, path } = splitPath(state, raw);
    const prefix = qualify(state, name, path.replace(/\/+$/, ""));
    return [...changed].some((item) => item === prefix || item.startsWith(`${prefix}/`));
  });
}

function ledgerReport(state: SnapshotState, changed: Set<string>) {
  if (state.ledger.length === 0) return [];
  const entries = state.ledger.map((entry) => {
    const marker = isStale(state, entry, changed) ? "stale" : "current";
    const paths = entry.paths.length > 0 ? ` (paths: ${entry.paths.join(", ")})` : "";
    return `- [${marker}] ${entry.case}: ${entry.status}; ${entry.evidence}${paths}`;
  });
  return ["", `Prior ledger (verdict: ${state.verdict}):`, ...entries];
}

/**
 * Captures every repository's candidate tree and reports changes since each one's last audited
 * tree, followed by the stored ledger with entries whose paths changed marked stale.
 */
export async function begin(scope: Scope, base?: string, repositories: RepositoryInput[] = []) {
  const { primaryPath, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, primaryPath, base);
    await addRepositories(state, scope, repositories);
    const sections: string[] = [];
    const changed = new Set<string>();
    for (const [name, repository] of Object.entries(state.repositories)) {
      repository.pending_tree = await captureTree(repository.path, directory, "pending.index");
      const previous = previousTree(repository);
      const changes = await changedPaths(
        repository.path,
        directory,
        previous,
        repository.pending_tree,
      );
      for (const path of changedPathList(changes)) changed.add(qualify(state, name, path));
      const role = name === state.primary ? "primary" : "additional";
      sections.push(
        [
          `Repository: ${name} (${role}) ${repository.path}`,
          `Previous tree: ${previous}`,
          `Pending tree: ${repository.pending_tree}`,
          "Changes:",
          changes || "(none)",
        ].join("\n"),
      );
    }
    await saveState(directory, state);
    return [
      `Iteration: ${state.iteration + 1}`,
      sections.join("\n\n"),
      ...ledgerReport(state, changed),
    ].join("\n");
  });
}

/** Returns the pending iteration's patch for the given repository paths, grouped by repository. */
export async function diff(scope: Scope, paths: string[]) {
  if (paths.length === 0) throw new SnapshotError("at least one path is required");
  const { primaryPath, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, primaryPath);
    const groups = new Map<string, string[]>();
    for (const raw of paths) {
      const { name, path } = splitPath(state, raw);
      groups.set(name, [...(groups.get(name) ?? []), path]);
    }
    const patches: string[] = [];
    for (const [name, group] of groups) {
      const repository = state.repositories[name];
      const pending = pendingTree(name, repository);
      const previous = previousTree(repository);
      const patch = await treeDiff(repository.path, directory, previous, pending, group);
      const body = patch || "(no changes)";
      patches.push(groups.size > 1 ? `Repository: ${name}\n${body}` : body);
    }
    return patches.join("\n");
  });
}

// Sandboxes sit beside their repository so parent-directory tool configuration (mise files and
// trust) applies to them as it does to the repository. Ceiling: an interrupted audit leaves its
// sandbox until the session's next acceptance_workspace or acceptance_finish removes it.
const sandboxPath = (directory: string, repository: RepositoryState) =>
  join(
    dirname(repository.path),
    `${basename(repository.path)}.acceptance-${basename(directory).slice(0, 8)}`,
  );

async function removeSandboxes(directory: string, state: SnapshotState) {
  for (const repository of Object.values(state.repositories)) {
    await rm(sandboxPath(directory, repository), { recursive: true, force: true });
  }
}

/**
 * Recreates a ready-to-run sandbox of each repository's pending tree: a standalone Git checkout
 * plus the repository's `.worktreeinclude` files, after its project setup hook has run.
 */
export async function workspace(scope: Scope) {
  const { primaryPath, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, primaryPath);
    const sections: string[] = [];
    for (const [name, repository] of Object.entries(state.repositories)) {
      const pending = pendingTree(name, repository);
      const path = sandboxPath(directory, repository);
      const previous = previousTree(repository);
      await materializeWorkspace(repository.path, directory, path, previous, pending);
      const copied = await copyIncludedFiles(repository.path, path);
      const hook = await runSetupHook(path, directory);
      sections.push(
        [
          `Repository: ${name}`,
          `Sandbox: ${path}`,
          `HEAD: previous tree ${previous}`,
          `Index and files: pending tree ${pending}`,
          `Included local files: ${copied.length > 0 ? copied.join(", ") : "(none)"}`,
          `Setup hook: ${hook}`,
        ].join("\n"),
      );
    }
    return sections.join("\n\n");
  });
}

/**
 * Stores the verdict and ledger, promotes every pending tree to audited, removes the sandboxes,
 * and reports `stable` only when every repository still matches its audited tree.
 */
export async function finish(
  scope: Scope,
  verdict: (typeof VERDICTS)[number],
  ledger: LedgerEntry[],
) {
  const { primaryPath, directory } = await prepare(scope);
  return locked(directory, async () => {
    const state = await validatedState(directory, primaryPath);
    for (const [name, repository] of Object.entries(state.repositories)) {
      pendingTree(name, repository);
    }
    for (const entry of ledger) for (const path of entry.paths) splitPath(state, path);
    const sections: string[] = [];
    let stable = true;
    for (const [name, repository] of Object.entries(state.repositories)) {
      const audited = pendingTree(name, repository);
      const current = await captureTree(repository.path, directory, "verify.index");
      const lines = [`Repository: ${name}`, `Audited tree: ${audited}`, `Current tree: ${current}`];
      if (audited === current) {
        lines.push("Status: stable");
      } else {
        stable = false;
        const changes = await changedPaths(repository.path, directory, audited, current);
        lines.push("Status: retry", "Changes since capture:", changes || "(none)");
      }
      sections.push(lines.join("\n"));
      repository.audited_tree = audited;
      repository.pending_tree = null;
    }
    state.iteration += 1;
    state.verdict = verdict;
    state.ledger = ledger;
    await saveState(directory, state);
    await removeSandboxes(directory, state);
    return [
      `Iteration: ${state.iteration}`,
      sections.join("\n\n"),
      `Result: ${stable ? "stable" : "retry"}`,
    ].join("\n");
  });
}
