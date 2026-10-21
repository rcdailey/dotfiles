import { watch } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";
import type { Plugin } from "@opencode/plugin";

// Appends the rules in ~/.config/opencode/session-permissions.jsonc to the session rules of
// sessions in use. Configured rules (global and repository) live on the agent; session rules
// evaluate after them, so these win where repository config would otherwise deny. A configured
// deny skips the permission `evaluate` hook, and user plugins load before the config plugin pushes
// agent rules, so neither hooks nor agent transforms can override it.
//
// MUST NOT touch idle sessions: a rule update bumps time_updated, which reorders the recent list.
// Sessions are reconciled when created, forked, or prompted, never in bulk. Updates run
// asynchronously, so a call made in the first moments after one of those events is unprotected.
// Rules from earlier file versions are tracked in storage and replaced rather than accumulated; a
// session rule identical to one of them is treated as managed.

type Rule = { action: string; resource: string; effect: "allow" | "ask" | "deny" };

const CONFIG_DIR = path.join(
  process.env.XDG_CONFIG_HOME || path.join(homedir(), ".config"),
  "opencode",
);
const CONFIG_FILE = "session-permissions.jsonc";

const sameRule = (a: Rule, b: Rule) =>
  a.action === b.action && a.resource === b.resource && a.effect === b.effect;

const readRules = async () =>
  Bun.JSONC.parse(await Bun.file(path.join(CONFIG_DIR, CONFIG_FILE)).text()) as Rule[];

export const SessionPermissions = {
  id: "local.session-permissions",
  async setup(ctx) {
    const storageKey = "managed";
    let rules: Rule[] = [];
    let managed: Rule[] = [];

    // Every rule any file version has contained, so long-idle sessions still shed stale ones.
    const reload = async () => {
      rules = await readRules();
      const previous = ((await ctx.storage.get(storageKey)) ?? []) as Rule[];
      managed = [
        ...previous,
        ...rules.filter((rule) => !previous.some((old) => sameRule(old, rule))),
      ];
      await ctx.storage.set(storageKey, managed);
    };

    const apply = async (sessionID: string, permissions: readonly Rule[] = []) => {
      const kept = permissions.filter((rule) => !managed.some((old) => sameRule(old, rule)));
      const next = [...kept, ...rules];
      const unchanged =
        next.length === permissions.length &&
        next.every((rule, index) => sameRule(rule, permissions[index]));
      if (unchanged) return;
      await ctx.session.update({ sessionID, permissions: next }).catch(console.error);
    };

    const applyCurrent = async (sessionID: string) =>
      apply(sessionID, (await ctx.session.get({ sessionID })).permissions);

    let queue = reload();
    await queue;
    const enqueue = (task: () => Promise<void>) => {
      queue = queue.then(task).catch(console.error);
    };

    // File edits reach each session at its next prompt; idle sessions stay untouched.
    const watcher = watch(CONFIG_DIR, (_, file) => {
      if (file === CONFIG_FILE) enqueue(reload);
    });
    // Not awaited: updating the session during prompt admission is unverified and could stall it.
    await ctx.session.hook("prompt", (event) => {
      const { sessionID } = event;
      enqueue(() => applyCurrent(sessionID));
    });
    const controller = new AbortController();
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        if (event.type === "session.created") {
          const { sessionID, permissions } = event.data;
          enqueue(() => apply(sessionID, permissions));
        } else if (event.type === "session.forked") {
          // Forks copy the parent's rules, but the event does not carry them.
          const { sessionID } = event.data;
          enqueue(() => applyCurrent(sessionID));
        }
      }
    })();
    return () => {
      watcher.close();
      controller.abort();
    };
  },
} satisfies Plugin.Plugin;

export default SessionPermissions;
