import { Database } from "bun:sqlite";
import { expect, test } from "bun:test";
import { chmod, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHost } from "./real-host.ts";

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

async function apiFixture() {
  const directory = await mkdtemp(join(tmpdir(), "opencode-prune-api-test-"));
  const executable = join(directory, "opencode");
  const script = `#!/usr/bin/env bash
set -euo pipefail
method="$2"
path="$3"
shift 3
params=()
while (($#)); do
  if [[ "$1" == "--param" ]]; then params+=(--data-urlencode "$2"); shift 2; else shift; fi
done
curl --fail --silent --show-error --get --request "${"${method^^}"}" \
  "${"${params[@]}"}" "$OPENCODE_API_URL$path"
`;
  await writeFile(executable, script);
  await chmod(executable, 0o755);

  const databasePath = join(directory, "sessions.db");
  const host = await createHost("{}", [], databasePath);
  const server = Bun.serve({
    port: 0,
    async fetch(request) {
      try {
        const url = new URL(request.url);
        if (url.pathname === "/api/session/active") {
          return Response.json(await host.session.active());
        }
        if (url.pathname === "/api/session" && request.method === "GET") {
          const parent = url.searchParams.get("parentID");
          const result = await host.session.list({
            cursor: url.searchParams.get("cursor") ?? undefined,
            limit: Number(url.searchParams.get("limit") ?? 100),
            order: url.searchParams.get("order") === "desc" ? "desc" : "asc",
            parentID: parent === "null" ? null : parent,
          });
          return Response.json(result);
        }
        const match = /^\/api\/session\/([^/]+)$/.exec(url.pathname);
        if (!match) return new Response("not found", { status: 404 });
        const sessionID = decodeURIComponent(match[1]);
        if (request.method === "DELETE") {
          await host.session.remove({ sessionID });
          return new Response(null, { status: 204 });
        }
        return Response.json(await host.session.get({ sessionID }));
      } catch (error) {
        return new Response(String(error), { status: 500 });
      }
    },
  });
  const env = {
    ...process.env,
    PATH: `${directory}:${process.env.PATH}`,
    OPENCODE_API_URL: server.url.origin,
    XDG_STATE_HOME: join(directory, "state"),
  };
  return { databasePath, directory, env, host, server };
}

async function importSession(
  host: Awaited<ReturnType<typeof createHost>>,
  input: {
    id: string;
    projectID: string;
    directory: string;
    updated: number;
    parentID?: string;
  },
) {
  await host.session.import({
    info: {
      id: input.id,
      parentID: input.parentID,
      projectID: input.projectID,
      cost: 0,
      tokens: { input: 0, output: 0, reasoning: 0, cache: { read: 0, write: 0 } },
      time: { created: input.updated, updated: input.updated },
      title: input.id,
      location: { directory: input.directory },
    },
    messages: [],
  });
}

async function runAsync(
  env: Record<string, string | undefined>,
  input: string,
): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  const process = Bun.spawn([command, "1"], { env, stdin: new Blob([input]) });
  const [exitCode, stdout, stderr] = await Promise.all([
    process.exited,
    new Response(process.stdout).text(),
    new Response(process.stderr).text(),
  ]);
  return { exitCode, stdout, stderr };
}

test("prunes a paginated cross-project tree through a real V2 host", async () => {
  const { databasePath, directory, env, host, server } = await apiFixture();
  try {
    const projectA = await host.session.create({
      location: { directory: join(directory, "project-a") },
    });
    const projectB = await host.session.create({
      location: { directory: join(directory, "project-b") },
    });
    await host.session.remove({ sessionID: projectA.id });
    await host.session.remove({ sessionID: projectB.id });

    const old = Date.now() - 3 * 86_400_000;
    await importSession(host, {
      id: "ses_old_root",
      projectID: projectA.projectID,
      directory: projectA.location.directory,
      updated: old,
    });
    await importSession(host, {
      id: "ses_old_child",
      parentID: "ses_old_root",
      projectID: projectA.projectID,
      directory: projectA.location.directory,
      updated: old,
    });
    for (let index = 0; index < 100; index++) {
      await importSession(host, {
        id: `ses_new_${index.toString().padStart(3, "0")}`,
        projectID: projectB.projectID,
        directory: projectB.location.directory,
        updated: Date.now(),
      });
    }
    const database = new Database(databasePath);
    database.run(
      "UPDATE session_v2 SET time_created = ?, time_updated = ? WHERE id LIKE 'ses_old_%'",
      [old, old],
    );
    database.close();

    const cancelled = await runAsync(env, "\n");
    expect(cancelled.exitCode).toBe(0);
    const preserved = await host.session.list({ parentID: null, limit: 200 });
    expect(preserved.data.map((session) => session.id)).toContain("ses_old_root");

    const deleted = await runAsync(env, "yes\n");
    expect(deleted.exitCode).toBe(0);
    expect(deleted.stdout).toContain("Deleted 1 session(s)");
    await expect(host.session.get({ sessionID: "ses_old_root" })).rejects.toThrow();
    await expect(host.session.get({ sessionID: "ses_old_child" })).rejects.toThrow();
    expect(await host.session.get({ sessionID: "ses_new_099" })).toBeDefined();

    const empty = await runAsync(env, "");
    expect(empty.stdout).toContain("No sessions have been inactive");
  } finally {
    server.stop(true);
    await host.close();
  }
}, 30_000);
