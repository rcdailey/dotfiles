import { dlopen, FFIType } from "bun:ffi";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

/** Fixed so each token rotation updates one account instead of adding another. Upper case
 * because CodexBar re-encodes account UUIDs that way. */
export const ACCOUNT_ID = "5A0C9E1B-7F3D-4C2A-9B8E-0D6C0DEBA12C";

type Account = { id: string; label: string; token: string; addedAt: number };
type TokenAccounts = { version: number; activeIndex: number; accounts: Account[] };
type Provider = { id: string; tokenAccounts?: TokenAccounts };
type Config = { providers?: Provider[] };

/** Mirrors CodexBarConfigStore.defaultURL so both apps and this plugin agree on one file. */
export function codexbarConfigPath(env = process.env, home = os.homedir()) {
  if (env.CODEXBAR_CONFIG?.trim()) return env.CODEXBAR_CONFIG.trim().replace(/^~(?=\/)/, home);
  const xdg = env.XDG_CONFIG_HOME?.trim();
  if (xdg && path.isAbsolute(xdg)) return path.join(xdg, "codexbar", "config.json");
  const xdgDefault = path.join(home, ".config", "codexbar", "config.json");
  const legacy = path.join(home, ".codexbar", "config.json");
  return !fs.existsSync(xdgDefault) && fs.existsSync(legacy) ? legacy : xdgDefault;
}

const LOCK_EX = 2;
const LOCK_NB = 4;
let flock: ((fd: number, operation: number) => number) | undefined;

// Node has no flock, and CodexBar locks with flock, so a lockfile library would not exclude it
function tryLock(fd: number) {
  flock ??= dlopen(process.platform === "darwin" ? "/usr/lib/libSystem.B.dylib" : "libc.so.6", {
    flock: { args: [FFIType.i32, FFIType.i32], returns: FFIType.i32 },
  }).symbols.flock;
  return flock(fd, LOCK_EX | LOCK_NB) === 0;
}

/**
 * Stores `token` as CodexBar's "OpenCode" Claude token account, which CodexBar uses as a plain
 * OAuth access token (it never refreshes token accounts). Follows CodexBar's best-effort writer:
 * skip when its config lock is held rather than wait, and retry on the next sync. Never creates
 * a config, so machines without CodexBar stay untouched. The selected account changes only when
 * this account is first added.
 */
export function syncToken(configPath: string, token: string, now: number) {
  if (!fs.existsSync(configPath)) return "skipped";
  const fd = fs.openSync(`${configPath}.lock`, "a", 0o600);
  try {
    if (!tryLock(fd)) return "busy";
    const config = JSON.parse(fs.readFileSync(configPath, "utf8")) as Config;
    const claude = config.providers?.find((provider) => provider.id === "claude");
    if (!claude) return "skipped";

    const tokenAccounts = claude.tokenAccounts ?? { version: 1, activeIndex: 0, accounts: [] };
    const accounts = tokenAccounts.accounts;
    const index = accounts.findIndex((account) => account.id.toUpperCase() === ACCOUNT_ID);
    if (index >= 0 && accounts[index].token === token) return "unchanged";
    if (index >= 0) {
      accounts[index] = { ...accounts[index], token };
    } else {
      accounts.push({ id: ACCOUNT_ID, label: "OpenCode", token, addedAt: Math.floor(now / 1000) });
      tokenAccounts.activeIndex = accounts.length - 1;
    }
    claude.tokenAccounts = tokenAccounts;

    // Rename keeps readers from seeing a partial file; CodexBar's watcher re-arms on rename
    const staged = `${configPath}.opencode-${process.pid}`;
    fs.writeFileSync(staged, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
    fs.renameSync(staged, configPath);
    return "written";
  } finally {
    fs.closeSync(fd);
  }
}
