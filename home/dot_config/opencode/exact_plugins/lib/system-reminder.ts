import type { Plugin } from "@opencode/plugin";
import {
  insertAnthropicReminders,
  REMINDER_BETA,
  supportsNativeReminders,
} from "./anthropic-reminders.ts";
import { decodeHistory, extendPrefix, isRecord } from "./reminder-history.ts";

// OpenCode loads only top-level plugin files and subdirectories with an index or server entry,
// so this helper directory is not loaded as a plugin.

/** The request's resolved model, independent of the provider selected through chezmoi. */
export type ReminderModel = { providerID: string; id: string };

/** A user-message boundary or a complete batch of tool results before the next model response. */
export type ReminderPhase = "turn" | "tool";

/**
 * Reminder policy, independent of provider syntax. Undefined omits this reminder at a boundary.
 * The delivery layer snapshots text when first sent; policy changes affect new boundaries only.
 * `primaryOnly` excludes child sessions. Unsupported models receive turn reminders only.
 */
export type Reminders = {
  text: (model: ReminderModel, phase: ReminderPhase) => string | undefined;
  primaryOnly?: boolean;
};

/** Delimit reminder text from ordinary user or tool content. */
export const wrap = (...sections: string[]) =>
  ["<system-reminder>", sections.join("\n\n"), "</system-reminder>"].join("\n");

/**
 * Register primary-loop delivery before the configured authentication plugin's HTTP hooks.
 * Native Claude reminders expire after the next user/tool-result message; other models get a
 * persistent reminder only at user boundaries. Neither path rewrites tool output or backfills
 * unseen historical boundaries. Persist before dispatch so retries and restarts replay exact text.
 * Start new sessions when adopting this protocol; previous plugins did not record sent reminders.
 * Journals retain reminder text and hashes, not transcript content. They grow with session history;
 * move to per-boundary storage if whole-journal reads/writes become an operational bottleneck.
 */
export async function injectReminders(ctx: Plugin.Context, reminders: Reminders) {
  const pending = new Map<string, Promise<unknown>>();
  const eligible = async (sessionID: Parameters<typeof ctx.session.get>[0]["sessionID"]) =>
    !reminders.primaryOnly || !(await ctx.session.get({ sessionID })).parentID;

  async function replay<T>(
    sessionID: string,
    model: ReminderModel,
    build: (lookup: (anchor: string, phase?: ReminderPhase) => string | undefined) => T,
  ): Promise<T> {
    const identity = encodeURIComponent(JSON.stringify([model.providerID, model.id]));
    const key = `reminders/v1/${sessionID}/${identity}`;
    const previous = pending.get(key) ?? Promise.resolve();
    const task = previous
      .catch(() => undefined)
      .then(async () => {
        const history = decodeHistory(await ctx.storage.get(key));
        let changed = false;
        const output = build((anchor, phase) => {
          if (Object.hasOwn(history.entries, anchor)) return history.entries[anchor] ?? undefined;
          if (phase === undefined) return;
          const text = reminders.text(model, phase);
          history.entries[anchor] = text ?? null;
          changed = true;
          return text;
        });
        if (changed) await ctx.storage.set(key, history);
        return output;
      });
    pending.set(key, task);
    try {
      return await task;
    } finally {
      if (pending.get(key) === task) pending.delete(key);
    }
  }

  await ctx.session.hook("context", async (event) => {
    if (supportsNativeReminders(event.model) || !(await eligible(event.sessionID))) return;
    event.messages = await replay(event.sessionID, event.model, (lookup) => {
      let prefix = "";
      let tail = event.messages.length - 1;
      while (tail >= 0 && event.messages[tail].role === "system") tail--;
      return event.messages.map((message, index) => {
        if (message.role === "system") return message;
        prefix = extendPrefix(prefix, message);
        if (message.role !== "user") return message;
        const text = lookup(prefix, index === tail ? "turn" : undefined);
        if (!text || message.content.some((part) => part.type === "text" && part.text === text)) {
          return message;
        }
        return { ...message, content: [...message.content, { type: "text" as const, text }] };
      });
    });
  });

  await ctx.session.hook(
    "http.request",
    async (event) => {
      if (event.kind !== "primary" || !supportsNativeReminders(event.model)) return;
      if (!(await eligible(event.sessionID))) return;
      const request = event.request;
      if (request.method !== "POST" || new URL(request.url).pathname !== "/v1/messages") {
        throw new Error("Native reminders require the Anthropic Messages endpoint");
      }
      const body: unknown = await request.clone().json();
      if (
        !isRecord(body) ||
        typeof body.model !== "string" ||
        !supportsNativeReminders({ providerID: event.model.providerID, id: body.model })
      )
        throw new Error("Native reminders require a supported Anthropic request model");
      const output = await replay(event.sessionID, event.model, (lookup) =>
        insertAnthropicReminders(body, lookup),
      );
      if (output === body) return;
      const headers = new Headers(request.headers);
      const betas = (headers.get("anthropic-beta") ?? "").split(",").map((item) => item.trim());
      headers.set(
        "anthropic-beta",
        [...new Set([...betas.filter(Boolean), REMINDER_BETA])].join(","),
      );
      for (const name of [
        "content-length",
        "content-encoding",
        "content-digest",
        "content-md5",
        "content-range",
        "digest",
        "etag",
      ])
        headers.delete(name);
      event.request = new Request(request, { headers, body: JSON.stringify(output) });
    },
    { providerID: "anthropic" },
  );
}
