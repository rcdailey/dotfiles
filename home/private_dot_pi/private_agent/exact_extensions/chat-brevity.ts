import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Turn-start chat guidance. pi persists the returned message in the session, so history replays
// byte-identically and the cached prefix never changes; only the new turn's tail is uncached.
// Text depends only on the model's provider, which keeps output deterministic per turn.
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
  "End a turn with work remaining only when progress needs the user; then state the current",
  "position and one next action. Do not invent a next step after completion. Never end a turn to",
  "announce a step you can take now, offer to continue, list decisions that block nothing, or",
  "report a milestone.",
].join(" ");

export const reminder = (provider: string | undefined) =>
  [
    "<system-reminder>",
    [CALIBRATION, provider === "anthropic" ? ANTHROPIC_BUDGET : DEFAULT_BUDGET, CLOSING].join(
      "\n\n",
    ),
    "</system-reminder>",
  ].join("\n");

export default function chatBrevity(pi: ExtensionAPI) {
  pi.on("before_agent_start", async (event, ctx) => {
    // Runs started by extension messages are not user turns; the last turn's reminder still applies.
    if (event.messageType !== "user") return;
    return {
      message: {
        customType: "chat-brevity",
        content: reminder(ctx.model?.provider),
        display: false,
      },
    };
  });
}
