import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Anthropic models drift to shell reads and scripted edits, which bypass the edit tool's
// exact-match check and diffs. pi persists the returned message in the session, so history replays
// byte-identically and the cached prefix never changes. Children re-run this hook, so subagents,
// which read most files, get it too.

export const REMINDER = [
  "<system-reminder>",
  [
    "Read, search, and edit files with the built-in file tools, not shell commands (sed, cat,",
    "heredocs) or scripts.",
  ].join(" "),
  "</system-reminder>",
].join("\n");

export default function fileTools(pi: ExtensionAPI) {
  pi.on("before_agent_start", async (event, ctx) => {
    // Runs started by extension messages are not user turns; the last turn's reminder still applies.
    if (event.messageType !== "user" || ctx.model?.provider !== "anthropic") return;
    return { message: { customType: "file-tools", content: REMINDER, display: false } };
  });
}
