import type { Plugin } from "@opencode-ai/plugin";

// The Chat Style rules in the system prompt lose to recency on long sessions, so restate the
// core constraint next to the newest user message. Injected at request time only: nothing is
// persisted to session storage and nothing renders in the TUI.

const PRIMARY_AGENTS = new Set(["build", "dispatch"]);

const REMINDER = [
  "<system-reminder>",
  "Chat brevity: you MUST answer first in plain words, under 6 lines, with no preamble, headers,",
  "or volunteered reasoning. Offer depth as a question instead of expanding.",
  "</system-reminder>",
].join("\n");

export const ChatBrevity: Plugin = async () => {
  return {
    // Compaction shares this hook, but its message slice ends on an assistant turn, so the
    // user-role gate keeps the reminder out of summarization input.
    "experimental.chat.messages.transform": async (_input, output) => {
      const last = output.messages.at(-1);
      if (last?.info.role !== "user") return;
      if (!PRIMARY_AGENTS.has(last.info.agent)) return;

      const anchor = last.parts.find((part) => part.type === "text");
      if (!anchor) return;

      last.parts.push({
        id: `${anchor.id}_brevity`,
        sessionID: anchor.sessionID,
        messageID: anchor.messageID,
        type: "text",
        text: REMINDER,
        synthetic: true,
      });
    },
  };
};
