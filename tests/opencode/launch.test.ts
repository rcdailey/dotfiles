import { expect, test } from "bun:test";
import { chmod, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const functions = join(import.meta.dir, "../../home/dot_config/exact_zsh/functions");

async function fixture(miseExit = 0) {
  const directory = await mkdtemp(join(tmpdir(), "opencode-launch-test-"));
  const log = join(directory, "calls.log");
  for (const name of ["mise", "opencode"]) {
    const executable = join(directory, name);
    const script = `#!/usr/bin/env bash
printf '%s %s\\n' '${name}' "$*" >> "$CALL_LOG"
${name === "mise" ? `exit ${miseExit}` : "exit 0"}
`;
    await writeFile(executable, script);
    await chmod(executable, 0o755);
  }
  const env = { ...process.env, PATH: `${directory}:${process.env.PATH}`, CALL_LOG: log };
  return { env, log };
}

function run(env: Record<string, string | undefined>, args: string[]) {
  return Bun.spawnSync(
    ["zsh", "-f", "-c", 'fpath=("$1"); autoload -Uz oc; shift; oc "$@"', "zsh", functions, ...args],
    { env },
  );
}

test("oc forwards ordinary arguments and exit status", async () => {
  const { env, log } = await fixture();
  const result = run(env, ["run", "two words"]);
  expect(result.exitCode).toBe(0);
  expect(await readFile(log, "utf8")).toBe("opencode run two words\n");
});

test("oc upgrades the mise package before plugins", async () => {
  const { env, log } = await fixture();
  const result = run(env, ["upgrade", "--yes"]);
  expect(result.exitCode).toBe(0);
  expect(await readFile(log, "utf8")).toBe(
    "mise upgrade npm:@opencode/cli --yes\nopencode plugin update\n",
  );
});

test("oc skips plugin updates after a failed CLI upgrade", async () => {
  const { env, log } = await fixture(7);
  const result = run(env, ["upgrade"]);
  expect(result.exitCode).toBe(7);
  expect(await readFile(log, "utf8")).toBe("mise upgrade npm:@opencode/cli\n");
});
