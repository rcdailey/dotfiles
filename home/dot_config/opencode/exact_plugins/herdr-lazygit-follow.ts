import { execFile } from "node:child_process";
import { mkdir, readdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import type { Plugin } from "@opencode/plugin";

/** One file per session, named by session ID and holding its directory. */
const SESSION_DIRS = path.join(
  process.env.XDG_STATE_HOME || path.join(homedir(), ".local", "state"),
  "opencode",
  "session-directories",
);
/** A resumed session past this age falls back to its pane's cwd until its next prompt. */
const STALE_AFTER_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * Publishes each session's working directory to SESSION_DIRS, so tools outside OpenCode can map a
 * session ID to the directory it works in. herdr-lazygit reads it to follow the focused pane's
 * session. A file is written when a session is created, moved (session_move, for example into a
 * new worktree), or prompted; a session left idle since this plugin loaded has none.
 *
 * A new or changed directory also runs `herdr-lazygit follow`: herdr reports only focus changes,
 * so without it the lazygit window would show a stale directory until the next tab switch.
 * `follow` ignores the call when the focused pane's repo is unchanged.
 */
export const HerdrLazygitFollow = {
  id: "local.herdr-lazygit-follow",
  async setup(ctx) {
    await mkdir(SESSION_DIRS, { recursive: true });
    // Sessions are rarely deleted, so session.deleted alone would let files pile up. Every prompt
    // rewrites a session's file, so its mtime is the session's last activity.
    const cutoff = Date.now() - STALE_AFTER_MS;
    for (const name of await readdir(SESSION_DIRS)) {
      const file = path.join(SESSION_DIRS, name);
      const { mtimeMs } = await stat(file).catch(() => ({ mtimeMs: Infinity }));
      if (mtimeMs < cutoff) await rm(file, { force: true });
    }

    const publish = async (sessionID: string, directory: string) => {
      const file = path.join(SESSION_DIRS, sessionID);
      const previous = await readFile(file, "utf8").catch(() => undefined);
      // Rename is atomic, so readers never see a partial path
      await writeFile(`${file}.tmp`, directory);
      await rename(`${file}.tmp`, file);
      if (previous === directory) return;
      // Missing outside a herdr setup; the window is optional, so failures are ignored
      execFile("herdr-lazygit", ["follow"], { timeout: 10_000 }, () => {});
    };

    let queue = Promise.resolve();
    const enqueue = (task: () => Promise<void>) => {
      queue = queue.then(task).catch(console.error);
    };

    await ctx.session.hook("prompt", ({ sessionID }) => {
      enqueue(async () =>
        publish(sessionID, (await ctx.session.get({ sessionID })).location.directory),
      );
    });
    const controller = new AbortController();
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        if (event.type === "session.created" || event.type === "session.moved") {
          const { sessionID, location } = event.data;
          enqueue(() => publish(sessionID, location.directory));
        } else if (event.type === "session.deleted") {
          const { sessionID } = event.data;
          enqueue(() => rm(path.join(SESSION_DIRS, sessionID), { force: true }));
        }
      }
    })();
    return () => controller.abort();
  },
} satisfies Plugin.Plugin;

export default HerdrLazygitFollow;
