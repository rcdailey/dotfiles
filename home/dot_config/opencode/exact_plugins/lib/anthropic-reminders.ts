import { extendPrefix, isRecord } from "./reminder-history.ts";
import type { ReminderModel, ReminderPhase } from "./system-reminder.ts";

/** Required for expiration, independently of ordinary mid-conversation system-message support. */
export const REMINDER_BETA = "mid-conversation-system-clear-at-2026-08-21";

/**
 * Native expiration is Anthropic-specific: Opus 4.8+ and Fable 5+ use it; other families fall back.
 * This assumes future versions of those families retain support. Revisit on a provider rejection.
 */
export function supportsNativeReminders(model: ReminderModel): boolean {
  if (model.providerID !== "anthropic") return false;
  const match = /^claude-(opus|fable)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?$/.exec(model.id);
  if (!match) return false;
  const major = Number(match[2]);
  const minor = Number(match[3] ?? 0);
  return major >= 5 || (match[1] === "opus" && major === 4 && minor >= 8);
}

type WireMessage = Record<string, unknown> & {
  role: "user" | "assistant" | "system";
  content: string | Record<string, unknown>[];
};

/**
 * Insert native reminders after complete user/tool-result groups, without moving cache markers.
 * The lookup records only the current boundary; historical boundaries replay stored text only.
 * System messages are excluded from anchors so independently registered reminder plugins compose.
 */
export function insertAnthropicReminders(
  body: Record<string, unknown>,
  lookup: (anchor: string, phase?: ReminderPhase) => string | undefined,
): Record<string, unknown> {
  if (
    !Array.isArray(body.messages) ||
    !body.messages.every(
      (message) =>
        isRecord(message) &&
        ["user", "assistant", "system"].includes(String(message.role)) &&
        (typeof message.content === "string" ||
          (Array.isArray(message.content) && message.content.every(isRecord))),
    )
  ) {
    throw new Error("Unsupported Anthropic messages; refusing to rewrite reminder history");
  }
  const messages = body.messages as WireMessage[];
  const output: WireMessage[] = [];
  const pending = new Set<string>();
  let prefix = "";
  let changed = false;
  for (let index = 0; index < messages.length; index++) {
    const message = messages[index];
    output.push(message);
    if (message.role === "system") continue;
    const blocks = Array.isArray(message.content) ? message.content : [];
    for (const block of blocks) {
      if (
        message.role === "assistant" &&
        block.type === "tool_use" &&
        typeof block.id === "string"
      ) {
        pending.add(block.id);
      }
      if (message.role === "user" && block.type === "tool_result") {
        pending.delete(String(block.tool_use_id));
      }
    }
    const content = Array.isArray(message.content)
      ? blocks.map(({ cache_control: _cache, ...block }) => block)
      : message.content;
    prefix = extendPrefix(prefix, { ...message, content });
    if (message.role !== "user" || pending.size > 0) continue;
    let boundary = index + 1;
    while (messages[boundary]?.role === "system") boundary++;
    const next = messages[boundary];
    if (next?.role === "user") continue;
    const phase =
      blocks.length > 0 && blocks.every((block) => block.type === "tool_result") ? "tool" : "turn";
    const text = lookup(prefix, next === undefined ? phase : undefined);
    if (!text) continue;
    const updates = messages.slice(index + 1, boundary);
    if (updates.some((item) => item.clear_at === "next_user_message" && item.content === text))
      continue;
    output.push(...updates, { role: "system", clear_at: "next_user_message", content: text });
    index = boundary - 1;
    changed = true;
  }
  return changed ? { ...body, messages: output } : body;
}
