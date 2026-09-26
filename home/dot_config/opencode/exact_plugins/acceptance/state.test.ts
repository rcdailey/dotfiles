import { afterEach, beforeEach, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { devNull, tmpdir } from "node:os";
import { join } from "node:path";
import { begin, diff, finish } from "./state.ts";

let root: string;
let repository: string;
const originalTmpdir = process.env.TMPDIR;

const git = (...args: string[]) =>
  execFileSync("git", args, {
    cwd: repository,
    encoding: "utf8",
    env: { ...process.env, GIT_CONFIG_GLOBAL: devNull, GIT_CONFIG_NOSYSTEM: "1" },
  }).trim();

const commit = () =>
  git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "Initial");

const session = (sessionID = "session-a") => ({ sessionID, directory: repository });

beforeEach(async () => {
  root = await mkdtemp(join(tmpdir(), "acceptance-test-"));
  repository = join(root, "repository");
  await mkdir(repository);
  await mkdir(join(root, "state"));
  process.env.TMPDIR = join(root, "state");
  git("init", "--quiet", "--initial-branch=main");
  await writeFile(join(repository, ".gitignore"), "ignored.txt\n");
  await writeFile(join(repository, "ignored.txt"), "ignored\n");
  await writeFile(join(repository, "staged.txt"), "staged\n");
  await writeFile(join(repository, "untracked.txt"), "untracked\n");
  git("add", "staged.txt");
});

afterEach(async () => {
  process.env.TMPDIR = originalTmpdir;
  await rm(root, { recursive: true, force: true });
});

test("repository without commits compares against the empty tree", async () => {
  const emptyTree = git("hash-object", "-t", "tree", devNull);

  const output = await begin(session());

  expect(output).toContain(`Previous tree: ${emptyTree}\n`);
  expect(output).toContain("Changes:\nA\t.gitignore\nA\tstaged.txt\nA\tuntracked.txt");
  expect(await diff(session(), ["staged.txt"])).toContain("+staged\n");
  expect(await finish(session())).toEndWith("Result: stable");
});

test("repository with commits compares against HEAD", async () => {
  commit();
  await writeFile(join(repository, "staged.txt"), "changed\n");
  const headTree = git("rev-parse", "HEAD^{tree}");

  const output = await begin(session());

  expect(output).toContain(`Previous tree: ${headTree}\n`);
  expect(output).toContain("Changes:\nA\t.gitignore\nM\tstaged.txt\nA\tuntracked.txt");
  expect(await finish(session())).toEndWith("Result: stable");
});

test("resumed begin reports only changes since the audited tree", async () => {
  await begin(session());
  await finish(session());
  commit();
  expect(await begin(session())).toContain("Iteration: 2\n");

  await writeFile(join(repository, "untracked.txt"), "edited\n");
  const output = await begin(session());

  expect(output).toContain("Iteration: 2\n");
  expect(output).toEndWith("Changes:\nM\tuntracked.txt");
});

test("finish reports retry when files change after begin", async () => {
  await begin(session());
  await writeFile(join(repository, "late.txt"), "late\n");

  const output = await finish(session());

  expect(output).toContain("Result: retry\nChanges since capture:\nA\tlate.txt");
  expect(await begin(session())).toEndWith("Changes:\nA\tlate.txt");
});

test("diff and finish require a pending iteration", async () => {
  await expect(diff(session(), ["staged.txt"])).rejects.toThrow("run acceptance_begin first");
  await expect(finish(session())).rejects.toThrow("run acceptance_begin first");
});

test("sessions keep separate state", async () => {
  await begin(session("session-a"));
  await finish(session("session-a"));

  const output = await begin(session("session-b"));

  expect(output).toContain("Iteration: 1\n");
  expect(output).toContain("A\tstaged.txt");
});

test("a session rejects a different repository", async () => {
  await begin(session());
  const other = join(root, "other");
  await mkdir(other);
  execFileSync("git", ["init", "--quiet"], { cwd: other });

  await expect(begin({ sessionID: "session-a", directory: other })).rejects.toThrow(
    "session belongs to",
  );
});

test("captures leave the repository index untouched", async () => {
  await begin(session());

  expect(git("diff", "--cached", "--name-only")).toBe("staged.txt");
});
