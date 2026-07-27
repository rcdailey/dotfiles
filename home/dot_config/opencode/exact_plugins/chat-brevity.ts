import type { Plugin } from "@opencode-ai/plugin";

// The Chat Style rules in the system prompt lose to recency on long sessions, so restate the
// core constraint at the very end of every request. The transform hook fires per LLM request
// (the prompt loop re-reads messages from the DB each step), so the mutation is in-memory only:
// nothing is persisted to session storage and nothing renders in the TUI.
//
// Turn start: the last message is the user's; append a synthetic text part to it.
// Mid-turn (tool loop): the last message is an assistant with finish "tool-calls"; append the
// reminder to the newest completed tool output so heavy tool stretches cannot bury it.
//
// Compaction shares this hook with the same empty input. Its message slice ends either on a
// completed turn (finish "stop", excluded by the finish gate) or mid-history where the user-role
// branch's agent gate applies before any summarization prompt, so summaries stay uncontaminated.

const PRIMARY_AGENTS = new Set(["build", "dispatch"]);

const REMINDER = [
  "<system-reminder>",
  "Chat brevity: you MUST answer first in plain words, under 6 lines, with no preamble, headers,",
  "or volunteered reasoning. Stop when answered: no trailing offers or follow-up questions.",
  "</system-reminder>",
].join("\n");

export const ChatBrevity: Plugin = async () => {
  return {
    "experimental.chat.messages.transform": async (_input, output) => {
      const last = output.messages.at(-1);
      if (!last || !PRIMARY_AGENTS.has(last.info.agent)) return;

      if (last.info.role === "user") {
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
        return;
      }

      if (last.info.role !== "assistant" || last.info.finish !== "tool-calls") return;

      const tool = last.parts.findLast(
        (part) => part.type === "tool" && part.state.status === "completed",
      );
      if (tool?.type !== "tool" || tool.state.status !== "completed") return;
      tool.state.output += `\n\n${REMINDER}`;
    },
  };
};
