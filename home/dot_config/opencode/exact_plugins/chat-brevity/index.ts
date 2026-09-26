import type { Plugin } from "@opencode/plugin";
import { injectReminders, wrap } from "../lib/system-reminder.ts";

// Subagents do not chat with the user, so only primary sessions receive this guidance.
// Source fragments join with spaces to avoid reproducing source line wrapping at runtime.

const CALIBRATION = [
  "Follow Chat Style. Default to the TLDR: answer, key reason, necessary caveats. Use STE",
  "principles for technical explanations. Assume engineering knowledge; clarify project concepts",
  "briefly inline.",
  "Use gathered context, not extra background research; investigate gaps that affect correctness.",
  "Do not invent intent. No extra tutorial or recap; stop when complete.",
].join(" ");

const ANTHROPIC_BUDGET = [
  "Hard length budget: under 120 words, unless the user asked for depth or the answer cannot fit.",
  "Verbosity is your dominant failure mode; length reads as padding, not thoroughness. Write the",
  "reply you would send if the user answered your draft with `TLDR`: same answer, same key reason,",
  "no scaffolding.",
].join(" ");

const DEFAULT_BUDGET = [
  "Optimize for first-pass comprehension, not minimum length; keep the one example or caveat that",
  "prevents a wrong inference.",
].join(" ");

const CLOSING = [
  "When ending a turn with work remaining, state the current position and one next action.",
  "Do not invent a next step after completion. Never end a turn to announce a step you",
  "can take now.",
].join(" ");

// Reinforcing CLOSING at every tool result can encourage premature stops. The underlying rule
// remains in the agent instructions when a native turn-start reminder expires.
/** Primary-session chat guidance; wording follows the model used for each request. */
export const ChatBrevity = {
  id: "local.chat-brevity",
  setup: (ctx) =>
    injectReminders(ctx, {
      text: (model, phase) => {
        const budget = model.providerID === "anthropic" ? ANTHROPIC_BUDGET : DEFAULT_BUDGET;
        return phase === "turn" ? wrap(CALIBRATION, budget, CLOSING) : wrap(CALIBRATION, budget);
      },
      primaryOnly: true,
    }),
} satisfies Plugin.Plugin;

export default ChatBrevity;
