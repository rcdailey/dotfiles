import { afterEach, beforeEach, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readFile, rm, utimes, writeFile } from "node:fs/promises";
import { devNull, homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { begin, diff, finish, workspace } from "./state.ts";

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

const done = (sessionID?: string) => finish(session(sessionID), "pass", []);

const sandboxOf = (output: string, name = "repository") =>
  output.match(new RegExp(`^Repository: ${name}\\nSandbox: (.+)$`, "m"))?.[1] ?? "";

async function createWiki() {
  const wiki = join(root, "wiki");
  await mkdir(wiki);
  const run = (...args: string[]) =>
    execFileSync("git", args, {
      cwd: wiki,
      encoding: "utf8",
      env: { ...process.env, GIT_CONFIG_GLOBAL: devNull, GIT_CONFIG_NOSYSTEM: "1" },
    });
  run("init", "--quiet", "--initial-branch=main");
  await writeFile(join(wiki, "page.md"), "page\n");
  run("add", "page.md");
  run("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "Initial");
  return wiki;
}

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
  expect(await done()).toEndWith("Result: stable");
});

test("repository with commits compares against HEAD", async () => {
  commit();
  await writeFile(join(repository, "staged.txt"), "changed\n");
  const headTree = git("rev-parse", "HEAD^{tree}");

  const output = await begin(session());

  expect(output).toContain(`Previous tree: ${headTree}\n`);
  expect(output).toContain("Changes:\nA\t.gitignore\nM\tstaged.txt\nA\tuntracked.txt");
  expect(await done()).toEndWith("Result: stable");
});

test("resumed begin reports only changes since the audited tree", async () => {
  await begin(session());
  await done();
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

  const output = await done();

  expect(output).toContain("Status: retry\nChanges since capture:\nA\tlate.txt");
  expect(output).toEndWith("Result: retry");
  expect(await begin(session())).toEndWith("Changes:\nA\tlate.txt");
});

test("diff and finish require a pending iteration", async () => {
  await expect(diff(session(), ["staged.txt"])).rejects.toThrow("run acceptance_begin");
  await expect(done()).rejects.toThrow("run acceptance_begin");
});

test("sessions keep separate state", async () => {
  await begin(session("session-a"));
  await done("session-a");

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

test("workspace stages the pending tree on top of the previous tree", async () => {
  commit();
  await writeFile(join(repository, "staged.txt"), "changed\n");
  await begin(session());

  const output = await workspace(session());

  const path = sandboxOf(output);
  expect(path).toBe(join(root, `repository.acceptance-${path.slice(-8)}`));
  const inWorkspace = (...args: string[]) =>
    execFileSync("git", args, { cwd: path, encoding: "utf8" }).trim();
  expect(inWorkspace("diff", "--cached", "--name-status")).toBe(
    "A\t.gitignore\nM\tstaged.txt\nA\tuntracked.txt",
  );
  expect(inWorkspace("status", "--porcelain", "--untracked-files=all")).not.toMatch(/^.[^ ]/m);
  expect(await readFile(join(path, "staged.txt"), "utf8")).toBe("changed\n");
  expect(existsSync(join(path, "ignored.txt"))).toBe(false);
});

test("workspace discards earlier edits and leaves the repository untouched", async () => {
  await begin(session());
  const path = sandboxOf(await workspace(session()));
  await writeFile(join(path, "staged.txt"), "rewritten by a hook\n");

  await workspace(session());

  expect(await readFile(join(path, "staged.txt"), "utf8")).toBe("staged\n");
  expect(git("diff", "--cached", "--name-only")).toBe("staged.txt");
  expect(await done()).toEndWith("Result: stable");
  expect(existsSync(path)).toBe(false);
});

test("workspace requires a pending iteration", async () => {
  await expect(workspace(session())).rejects.toThrow("run acceptance_begin");
});

test("workspace copies only ignored files that .worktreeinclude lists", async () => {
  await writeFile(join(repository, ".gitignore"), "ignored.txt\n.env\nnode_modules/\n");
  await writeFile(join(repository, ".worktreeinclude"), ".env\nnode_modules/\nuntracked.txt\n");
  await writeFile(join(repository, ".env"), "secret\n");
  await mkdir(join(repository, "node_modules", "dep"), { recursive: true });
  await writeFile(join(repository, "node_modules", "dep", "index.js"), "dep\n");
  await begin(session());

  const output = await workspace(session());

  const path = sandboxOf(output);
  expect(output).toContain("Included local files: .env, node_modules/\n");
  expect(await readFile(join(path, ".env"), "utf8")).toBe("secret\n");
  expect(existsSync(join(path, "node_modules", "dep", "index.js"))).toBe(true);
  expect(existsSync(join(path, "ignored.txt"))).toBe(false);
});

const hasWt = (() => {
  try {
    execFileSync("wt", ["--version"]);
    return true;
  } catch {
    return false;
  }
})();

test("workspace reports a missing recipe", async () => {
  await begin(session());
  expect(await workspace(session())).toContain("Setup hook: absent (no .config/wt.toml)");
});

test.skipIf(!hasWt)("workspace keeps user worktrunk hooks out (requires wt)", async () => {
  const originalConfigHome = process.env.XDG_CONFIG_HOME;
  const configHome = join(root, "config");
  await mkdir(join(configHome, "worktrunk"), { recursive: true });
  await writeFile(
    join(configHome, "worktrunk", "config.toml"),
    '[pre-start]\nuser = "touch user-hook-ran"\n',
  );
  await mkdir(join(repository, ".config"));
  await writeFile(join(repository, ".config", "wt.toml"), 'pre-start = "touch hook-ran"\n');
  const originalMiseConfig = process.env.MISE_CONFIG_DIR;
  // Keeps mise's global tool config (which provides wt) while worktrunk reads the fake one.
  process.env.MISE_CONFIG_DIR ??= join(originalConfigHome ?? join(homedir(), ".config"), "mise");
  process.env.XDG_CONFIG_HOME = configHome;
  try {
    await begin(session());
    const path = sandboxOf(await workspace(session()));
    expect(existsSync(join(path, "hook-ran"))).toBe(true);
    expect(existsSync(join(path, "user-hook-ran"))).toBe(false);

    // Proves the user config is live: worktrunk runs it when the plugin's exclusion is absent.
    execFileSync("wt", ["hook", "pre-start", "--foreground", "--yes"], { cwd: path });
    expect(existsSync(join(path, "user-hook-ran"))).toBe(true);
  } finally {
    process.env.XDG_CONFIG_HOME = originalConfigHome;
    if (originalMiseConfig === undefined) delete process.env.MISE_CONFIG_DIR;
    else process.env.MISE_CONFIG_DIR = originalMiseConfig;
  }
});

test.skipIf(!hasWt)("workspace runs project setup hooks (requires wt)", async () => {
  await mkdir(join(repository, ".config"));
  await writeFile(join(repository, ".config", "wt.toml"), 'pre-start = "touch hook-ran"\n');
  await begin(session());
  const output = await workspace(session());

  expect(output).toContain("Setup hook: ran");
  expect(existsSync(join(sandboxOf(output), "hook-ran"))).toBe(true);
  expect(existsSync(join(repository, "hook-ran"))).toBe(false);
});

test.skipIf(!hasWt)("workspace reports a failing setup hook (requires wt)", async () => {
  await mkdir(join(repository, ".config"));
  await writeFile(join(repository, ".config", "wt.toml"), 'pre-start = "exit 3"\n');
  await begin(session());

  expect(await workspace(session())).toContain("Setup hook: failed");
});

test("named repositories are captured, diffed by prefix, and remembered on resume", async () => {
  commit();
  const wiki = await createWiki();
  await writeFile(join(wiki, "page.md"), "edited\n");

  const output = await begin(session(), undefined, [{ path: "../wiki" }]);

  expect(output).toContain(`Repository: repository (primary) ${repository}\n`);
  expect(output).toContain(`Repository: wiki (additional) ${wiki}\n`);
  expect(output).toEndWith("Changes:\nM\tpage.md");
  const both = await diff(session(), ["wiki:page.md", "staged.txt"]);
  expect(both).toContain("Repository: wiki\n");
  expect(both).toContain("+edited\n");
  expect(await diff(session(), ["wiki:page.md"])).not.toContain("Repository:");
  await expect(diff(session(), ["docs:page.md"])).rejects.toThrow("unknown repository docs");
  expect(await done()).toEndWith("Result: stable");

  await writeFile(join(wiki, "page.md"), "again\n");
  const resumed = await begin(session());

  expect(resumed).toContain("Iteration: 2\n");
  expect(resumed).toContain("Changes:\n(none)\n\nRepository: wiki");
  expect(resumed).toEndWith("Changes:\nM\tpage.md");
});

test("a resumed begin adds a repository without restarting the others", async () => {
  await begin(session());
  await done();
  const wiki = await createWiki();
  await writeFile(join(wiki, "page.md"), "edited\n");

  const output = await begin(session(), undefined, [{ path: wiki }]);

  expect(output).toContain("Iteration: 2\n");
  expect(output).toContain("Changes:\n(none)\n\nRepository: wiki");
  expect(output).toEndWith("Changes:\nM\tpage.md");
  expect(await diff(session(), ["wiki:page.md"])).toContain("+edited\n");
});

test("finish reports retry when a named repository changes after begin", async () => {
  const wiki = await createWiki();
  await begin(session(), undefined, [{ path: wiki }]);
  await writeFile(join(wiki, "late.md"), "late\n");

  const output = await done();

  expect(output).toContain("Repository: wiki\n");
  expect(output).toContain("Status: retry\nChanges since capture:\nA\tlate.md");
  expect(output).toEndWith("Result: retry");
});

test("workspace prepares a sandbox for every repository", async () => {
  const wiki = await createWiki();
  await begin(session(), undefined, [{ path: wiki }]);

  const output = await workspace(session());

  expect(await readFile(join(sandboxOf(output, "wiki"), "page.md"), "utf8")).toBe("page\n");
  expect(existsSync(join(sandboxOf(output), "staged.txt"))).toBe(true);
});

test("workspace removes other sessions' abandoned sandboxes and keeps recent ones", async () => {
  const abandoned = join(root, "repository.acceptance-abandone");
  const recent = join(root, "repository.acceptance-recent00");
  await mkdir(abandoned);
  await mkdir(recent);
  const dayAgo = new Date(Date.now() - 25 * 60 * 60 * 1000);
  await utimes(abandoned, dayAgo, dayAgo);
  await begin(session());

  await workspace(session());

  expect(existsSync(abandoned)).toBe(false);
  expect(existsSync(recent)).toBe(true);
});

const hasMise = (() => {
  try {
    execFileSync("mise", ["--version"]);
    return true;
  } catch {
    return false;
  }
})();

test.skipIf(!hasWt || !hasMise)(
  "setup hooks get the sandbox's mise env (requires wt, mise)",
  async () => {
    const originalTrusted = process.env.MISE_TRUSTED_CONFIG_PATHS;
    await writeFile(join(repository, "mise.toml"), '[env]\nSANDBOX_PROBE = "from-mise"\n');
    await mkdir(join(repository, ".config"));
    await writeFile(
      join(repository, ".config", "wt.toml"),
      'pre-start = "printf %s \\"$SANDBOX_PROBE\\" > probe.txt"\n',
    );
    process.env.MISE_TRUSTED_CONFIG_PATHS = root;
    try {
      await begin(session());
      const output = await workspace(session());

      expect(output).toContain("Setup hook: ran");
      expect(await readFile(join(sandboxOf(output), "probe.txt"), "utf8")).toBe("from-mise");
    } finally {
      if (originalTrusted === undefined) delete process.env.MISE_TRUSTED_CONFIG_PATHS;
      else process.env.MISE_TRUSTED_CONFIG_PATHS = originalTrusted;
    }
  },
);

test("a named repository cannot reuse a repository name", async () => {
  const twin = join(root, "nested", "repository");
  await mkdir(twin, { recursive: true });
  execFileSync("git", ["init", "--quiet"], { cwd: twin });

  await expect(begin(session(), undefined, [{ path: twin }])).rejects.toThrow(
    "repository name repository is already used",
  );
});

test("resumed begin returns the stored ledger and marks changed cases stale", async () => {
  const wiki = await createWiki();
  await begin(session(), undefined, [{ path: wiki }]);
  await finish(session(), "fail", [
    { case: "docs match", status: "fail", evidence: "flag missing", paths: ["wiki:page.md"] },
    { case: "untouched", status: "pass", evidence: "test ran", paths: ["staged.txt"] },
  ]);
  await writeFile(join(wiki, "page.md"), "fixed\n");

  const output = await begin(session());

  expect(output).toContain("Prior ledger (verdict: fail):\n");
  expect(output).toContain("- [stale] docs match: fail; flag missing (paths: wiki:page.md)");
  expect(output).toContain("- [current] untouched: pass; test ran (paths: staged.txt)");
});

test("finish rejects ledger paths in unknown repositories", async () => {
  await begin(session());
  const ledger = [{ case: "c", status: "pass" as const, evidence: "e", paths: ["docs:a.md"] }];

  await expect(finish(session(), "pass", ledger)).rejects.toThrow("unknown repository docs");
});

test("state from the previous schema requires a fresh audit", async () => {
  await begin(session());
  const state = join(
    root,
    "state",
    "opencode-acceptance",
    createHash("sha256").update("session-a").digest("hex"),
    "state.json",
  );
  await writeFile(state, JSON.stringify({ version: 1 }));

  await expect(begin(session())).rejects.toThrow("a fresh audit is required");
});

test("captures leave the repository index untouched", async () => {
  await begin(session());

  expect(git("diff", "--cached", "--name-only")).toBe("staged.txt");
});
