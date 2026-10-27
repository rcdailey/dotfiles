import { afterEach, beforeEach, expect, test } from "bun:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { ACCOUNT_ID, syncToken } from "./sync.ts";

let dir: string;
let configPath: string;

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "codexbar-token-"));
  configPath = path.join(dir, "config.json");
});

afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

const writeConfig = (config: unknown) => fs.writeFileSync(configPath, JSON.stringify(config));
const readConfig = () => JSON.parse(fs.readFileSync(configPath, "utf8"));
const claude = (config: { providers: { id: string }[] }) =>
  config.providers.find((provider) => provider.id === "claude") as Record<string, any>;

const baseConfig = () => ({
  version: 1,
  providers: [
    { id: "codex", enabled: false },
    { id: "claude", enabled: true, source: "oauth" },
  ],
});

test("adds the OpenCode account as active and keeps unrelated config", () => {
  writeConfig(baseConfig());

  expect(syncToken(configPath, "sk-ant-oat-one", 1_000_000)).toBe("written");

  const config = readConfig();
  expect(config.providers[0]).toEqual({ id: "codex", enabled: false });
  expect(claude(config)).toMatchObject({ enabled: true, source: "oauth" });
  expect(claude(config).tokenAccounts).toEqual({
    version: 1,
    activeIndex: 0,
    accounts: [{ id: ACCOUNT_ID, label: "OpenCode", token: "sk-ant-oat-one", addedAt: 1000 }],
  });
  expect(fs.statSync(configPath).mode & 0o777).toBe(0o600);
});

test("replaces a rotated token in place without changing the selected account", () => {
  const config = baseConfig();
  const manual = { id: "11111111-1111-1111-1111-111111111111", label: "Manual", token: "x" };
  // CodexBar re-encodes UUIDs in upper case; a lower-case match would add a duplicate
  const ours = { id: ACCOUNT_ID.toLowerCase(), label: "OpenCode", token: "old", addedAt: 5 };
  Object.assign(claude(config), {
    tokenAccounts: { version: 1, activeIndex: 0, accounts: [manual, ours] },
  });
  writeConfig(config);

  expect(syncToken(configPath, "sk-ant-oat-two", 9_000_000)).toBe("written");

  const accounts = claude(readConfig()).tokenAccounts;
  expect(accounts.activeIndex).toBe(0);
  expect(accounts.accounts).toEqual([manual, { ...ours, token: "sk-ant-oat-two" }]);
});

test("leaves the file untouched when the token is unchanged", () => {
  writeConfig(baseConfig());
  syncToken(configPath, "sk-ant-oat-one", 1_000_000);
  const before = fs.statSync(configPath).ino;

  expect(syncToken(configPath, "sk-ant-oat-one", 2_000_000)).toBe("unchanged");
  expect(fs.statSync(configPath).ino).toBe(before);
});

test("does nothing when CodexBar has no config or no Claude provider", () => {
  expect(syncToken(configPath, "sk-ant-oat-one", 1)).toBe("skipped");
  expect(fs.existsSync(configPath)).toBe(false);

  writeConfig({ version: 1, providers: [{ id: "codex" }] });
  expect(syncToken(configPath, "sk-ant-oat-one", 1)).toBe("skipped");
  expect(readConfig()).toEqual({ version: 1, providers: [{ id: "codex" }] });
});

// CodexBar serializes its own config writes with flock on `config.json.lock`
test("skips while another process holds CodexBar's config lock", async () => {
  writeConfig(baseConfig());
  const holder = Bun.spawn(
    [
      "python3",
      "-c",
      "import fcntl,sys; f=open(sys.argv[1],'a'); fcntl.flock(f,fcntl.LOCK_EX); " +
        "print('locked',flush=True); sys.stdin.read()",
      `${configPath}.lock`,
    ],
    { stdin: "pipe", stdout: "pipe" },
  );
  try {
    const reader = holder.stdout.getReader();
    expect(new TextDecoder().decode((await reader.read()).value)).toContain("locked");

    expect(syncToken(configPath, "sk-ant-oat-one", 1)).toBe("busy");
    expect(claude(readConfig()).tokenAccounts).toBeUndefined();
  } finally {
    holder.stdin.end();
    await holder.exited;
  }

  expect(syncToken(configPath, "sk-ant-oat-one", 1)).toBe("written");
});
