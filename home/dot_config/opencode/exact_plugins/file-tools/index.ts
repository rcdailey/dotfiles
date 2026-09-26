import type { Plugin } from "@opencode/plugin";
import { injectReminders, wrap } from "../lib/system-reminder.ts";

// Anthropic models drift to shell reads and scripted edits, which bypass the edit tool's
// exact-match check, formatters, and diffs. Subagents read most files, so they get it too.

const REMINDER = wrap(
  [
    "Read, search, and edit files with the built-in file tools, not shell commands (sed, cat,",
    "heredocs) or scripts.",
  ].join(" "),
);

/** File-tool guidance for Anthropic requests in both primary and child sessions. */
export const FileTools = {
  id: "local.file-tools",
  setup: (ctx) =>
    injectReminders(ctx, {
      text: (model) => (model.providerID === "anthropic" ? REMINDER : undefined),
    }),
} satisfies Plugin.Plugin;

export default FileTools;
