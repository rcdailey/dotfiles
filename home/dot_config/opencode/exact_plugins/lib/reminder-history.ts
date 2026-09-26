import { createHash } from "node:crypto";

/**
 * Persisted reminder text, keyed by the source-history prefix where it was first sent.
 * Null records a deliberate omission. Existing entries never change when wording changes.
 * Retain old prefixes for undo and provider switches; compacted prefixes start fresh.
 */
export type ReminderHistory = {
  version: 1;
  entries: Record<string, string | null>;
};

/** Reject incompatible or corrupt storage rather than silently rewriting a session's history. */
export function decodeHistory(value: unknown): ReminderHistory {
  if (value === undefined) return { version: 1, entries: {} };
  if (
    !isRecord(value) ||
    value.version !== 1 ||
    !isRecord(value.entries) ||
    !Object.entries(value.entries).every(
      ([key, text]) => /^[a-f0-9]{64}$/.test(key) && (text === null || typeof text === "string"),
    )
  ) {
    throw new Error("Invalid reminder history; refusing to replace previously sent reminders");
  }
  return value as ReminderHistory;
}

/** Extend a content-addressed prefix without storing user messages or tool output. */
export function extendPrefix(previous: string, message: unknown): string {
  const canonical = JSON.stringify(message, (_key, value) =>
    isRecord(value)
      ? Object.fromEntries(
          Object.entries(value).sort(([left], [right]) =>
            left < right ? -1 : left > right ? 1 : 0,
          ),
        )
      : value,
  );
  return createHash("sha256").update(previous).update(canonical).digest("hex");
}

/** Narrow JSON-shaped objects at the storage and provider-request boundaries. */
export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
