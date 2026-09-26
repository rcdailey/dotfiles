import type { Message, TextPart } from "@opencode/ai";
import type { Plugin } from "@opencode/plugin";

// OpenCode loads only top-level plugin files and subdirectories with an index or server entry,
// so this helper directory is not loaded as a plugin.

/**
 * Guidance a plugin reinjects into model context: `turn` after each user message, `tool` after
 * each tool result, so long tool loops cannot bury it. Each plugin deduplicates by its own text,
 * so several plugins can append separate `<system-reminder>` blocks to the same message.
 * `primaryOnly` skips child sessions (subagents).
 */
export type Reminders = {
  turn: string;
  tool: string;
  primaryOnly?: boolean;
};

export const wrap = (...sections: string[]) =>
  ["<system-reminder>", sections.join("\n\n"), "</system-reminder>"].join("\n");

type MutableMessage = {
  role: Message["role"];
  content: Array<Message["content"][number]>;
};
type MutableToolResult = {
  type: "tool-result";
  result:
    | { type: "content"; value: Array<{ type: "text"; text: string } | Record<string, unknown>> }
    | { type: "text" | "json" | "error"; value: unknown };
};

const isText = (part: unknown): part is TextPart =>
  Boolean(part && typeof part === "object" && Reflect.get(part, "type") === "text");

const isToolResult = (part: unknown): part is MutableToolResult =>
  Boolean(part && typeof part === "object" && Reflect.get(part, "type") === "tool-result");

function appendToolReminder(part: MutableToolResult, reminder: string) {
  const result = part.result;
  if (result.type === "error") return;
  if (result.type === "content") {
    if (result.value.some((item) => isText(item) && item.text === reminder)) return;
    result.value.push({ type: "text", text: reminder });
    return;
  }
  if (result.type === "text" && typeof result.value === "string") {
    if (!result.value.includes(reminder)) result.value += `\n\n${reminder}`;
    return;
  }
  if (result.type === "json") {
    const serialized = JSON.stringify(result.value) ?? String(result.value);
    part.result = {
      type: "content",
      value: [
        { type: "text", text: serialized },
        { type: "text", text: reminder },
      ],
    };
  }
}

export async function injectReminders(ctx: Plugin.Context, reminders: Reminders) {
  await ctx.session.hook("context", async (event) => {
    if (reminders.primaryOnly) {
      const session = await ctx.session.get({ sessionID: event.sessionID }).catch(() => undefined);
      if (!session || session.parentID) return;
    }

    const messages = event.messages as MutableMessage[];
    const last = messages.at(-1);
    if (!last) return;

    if (last.role === "user") {
      if (!last.content.some(isText)) return;
      if (last.content.some((part) => isText(part) && part.text === reminders.turn)) return;
      last.content.push({ type: "text", text: reminders.turn });
      return;
    }

    if (last.role !== "tool") return;
    const tool = (last.content as unknown[]).findLast(isToolResult);
    if (tool) appendToolReminder(tool, reminders.tool);
  });
}
