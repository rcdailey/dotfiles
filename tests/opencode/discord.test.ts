import { expect, test } from "bun:test";
import { chmod, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const exporter = join(
  import.meta.dir,
  "../../home/dot_config/opencode/exact_skills/discord-chat/executable_export.py",
);

async function fixture() {
  const directory = await mkdtemp(join(tmpdir(), "discord-export-test-"));
  const mise = join(directory, "mise");
  const log = join(directory, "args.log");
  await writeFile(mise, '#!/usr/bin/env bash\nprintf \'%s\\n\' "$@" > "$CALL_LOG"\n');
  await chmod(mise, 0o755);
  return {
    env: {
      ...process.env,
      PATH: `${directory}:${process.env.PATH}`,
      CALL_LOG: log,
      DISCORD_TOKEN: "test-token",
    },
    log,
  };
}

test("exports the week ending at a linked Discord message", async () => {
  const { env, log } = await fixture();
  const url =
    "https://discord.com/channels/673534664354430999/1097927240978808882/" + "1543962458941685761";
  const result = Bun.spawnSync(["python3", exporter, url], { env });

  expect(result.exitCode).toBe(0);
  expect(result.stdout.toString()).toBe(
    "/tmp/opencode/discord-1097927240978808882-1543962458941685761.txt\n",
  );
  expect((await readFile(log, "utf8")).split("\n")).toEqual([
    "exec",
    "--",
    "DiscordChatExporter.Cli",
    "export",
    "--channel",
    "1097927240978808882",
    "--format",
    "PlainText",
    "--output",
    "/tmp/opencode/discord-1097927240978808882-1543962458941685761.txt",
    "--after",
    "2026-08-24T12:35:36.647Z",
    "--before",
    "2026-08-31T12:35:36.647Z",
    "--utc",
    "",
  ]);
});

test("stops before invoking mise when the Discord token is absent", async () => {
  const { env, log } = await fixture();
  delete env.DISCORD_TOKEN;
  const result = Bun.spawnSync(["python3", exporter, "https://discord.com/channels/1/2"], { env });

  expect(result.exitCode).toBe(1);
  expect(result.stderr.toString()).toContain("DISCORD_TOKEN is not set");
  await expect(readFile(log, "utf8")).rejects.toThrow();
});
