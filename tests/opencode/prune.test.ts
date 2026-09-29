import { expect, test } from "bun:test";
import { chmod, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const command = join(
  import.meta.dir,
  "../../home/dot_local/bin/executable_opencode-prune-sessions",
);

async function fixture() {
  const directory = await mkdtemp(join(tmpdir(), "opencode-prune-test-"));
  const executable = join(directory, "opencode");
  const log = join(directory, "calls.log");
  const session = JSON.stringify({
    id: "ses_old",
    title: "Old session",
    projectID: "project",
    location: { directory: "/project" },
    time: { updated: "2000-01-01T00:00:00Z" },
  });
  const script = `#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CALL_LOG"
if [[ "$*" == *"delete /api/session/ses_old"* ]]; then exit 0; fi
if [[ "$*" == *"get /api/session/ses_old"* ]]; then printf '%s\\n' '${session}'; exit 0; fi
if [[ "$*" == *"get /api/session/active"* ]]; then printf '%s\\n' '{}'; exit 0; fi
if [[ "$*" == *"parentID=ses_old"* ]]; then printf '%s\\n' '{"data":[],"cursor":{}}'; exit 0; fi
printf '%s\\n' '{"data":[${session}],"cursor":{}}'
`;
  await writeFile(executable, script);
  await chmod(executable, 0o755);
  const env = {
    ...process.env,
    PATH: `${directory}:${process.env.PATH}`,
    CALL_LOG: log,
    XDG_STATE_HOME: join(directory, "state"),
  };
  return { env, log };
}

test("pruning defaults to no without deleting", async () => {
  const { env, log } = await fixture();
  const result = Bun.spawnSync([command, "1"], { env, stdin: new Blob([]) });
  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("No sessions deleted");
  expect(await readFile(log, "utf8")).not.toContain("delete /api/session");
});

test("pruning rechecks and deletes an old session tree", async () => {
  const { env, log } = await fixture();
  const result = Bun.spawnSync([command, "1"], { env, stdin: new Blob(["yes\n"]) });
  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toContain("Deleted 1 session(s)");
  const calls = await readFile(log, "utf8");
  expect(calls).toContain("get /api/session/ses_old");
  expect(calls).toContain("parentID=ses_old");
  expect(calls).toContain("delete /api/session/ses_old");
});

async function failureFixture(interruptSecond = false) {
  const directory = await mkdtemp(join(tmpdir(), "opencode-prune-failure-test-"));
  const executable = join(directory, "opencode");
  const log = join(directory, "calls.log");
  const session = (id: string) =>
    JSON.stringify({
      id,
      title: id,
      projectID: "project",
      location: { directory: "/project" },
      time: { updated: 946684800000 },
    });
  const interrupt = interruptSecond ? 'kill -INT "$PPID"; sleep 1; exit 130' : "exit 9";
  const script = `#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CALL_LOG"
if [[ "$*" == *"get /api/session/active"* ]]; then printf '%s\\n' '{}'; exit 0; fi
if [[ "$*" == *"get /api/session/ses_one"* ]]; then printf '%s\\n' '${session("ses_one")}'; exit 0; fi
if [[ "$*" == *"get /api/session/ses_two"* ]]; then printf '%s\\n' '${session("ses_two")}'; exit 0; fi
if [[ "$*" == *"parentID=ses_"* ]]; then printf '%s\\n' '{"data":[],"cursor":{}}'; exit 0; fi
if [[ "$*" == *"delete /api/session/ses_one"* ]]; then exit 0; fi
if [[ "$*" == *"delete /api/session/ses_two"* ]]; then ${interrupt}; fi
printf '%s\\n' '{"data":[${session("ses_one")},${session("ses_two")}],"cursor":{}}'
`;
  await writeFile(executable, script);
  await chmod(executable, 0o755);
  const env = {
    ...process.env,
    PATH: `${directory}:${process.env.PATH}`,
    CALL_LOG: log,
    XDG_STATE_HOME: join(directory, "state"),
  };
  return { env, log };
}

test("pruning reports a partial deletion failure and continues", async () => {
  const { env, log } = await failureFixture();
  const result = Bun.spawnSync([command, "1"], { env, stdin: new Blob(["yes\n"]) });
  expect(result.exitCode).toBe(1);
  expect(result.stdout.toString()).toContain("Deleted 1 session(s)");
  expect(result.stderr.toString()).toContain("Failed to delete ses_two");
  expect(await readFile(log, "utf8")).toContain("delete /api/session/ses_one");
});

test("interruption preserves completed deletions", async () => {
  const { env, log } = await failureFixture(true);
  const result = Bun.spawnSync([command, "1"], { env, stdin: new Blob(["yes\n"]) });
  expect(result.exitCode).toBe(130);
  expect(result.stderr.toString()).toContain("completed deletions were preserved");
  const calls = await readFile(log, "utf8");
  expect(calls).toContain("delete /api/session/ses_one");
  expect(calls).toContain("delete /api/session/ses_two");
});
